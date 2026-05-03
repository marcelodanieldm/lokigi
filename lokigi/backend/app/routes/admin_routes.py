"""routes/admin_routes.py — Multi-seat organization & member management.

Endpoints
─────────
HTML panels
  GET  /admin/members              Panel A: member management (Jinja2 + HTMX)
  GET  /admin/members/accept       Accept invite via token (redirect)

Member API (JSON + HTMX partial responses)
  POST   /api/v1/admin/members/invite            Invite a new member by email
  PATCH  /api/v1/admin/members/{member_id}/role  Update role (HTMX)
  DELETE /api/v1/admin/members/{member_id}       Remove member (HTMX)
  POST   /api/v1/admin/org                       Create organization

CEO KPI endpoints (X-CEO-Key guarded)
  GET  /api/v1/ceo/subscription-kpis             Expansion revenue, user-to-location ratio, churn by plan
  POST /api/v1/admin/subscriptions/run-expiry    Manually trigger daily expiry check
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import (
    GoogleConnection,
    LifecycleEvent,
    OrgMember,
    Organization,
    SubscriptionProfile,
    User,
)
from app.rbac import ROLE_PERMISSIONS, ROLE_TIER, RBACContext, require_permission
from app.subscription_manager import SubscriptionManager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin", "ceo"])
templates = Jinja2Templates(directory="app/templates")

INVITE_TTL_HOURS = 72


# ── CEO auth guard ────────────────────────────────────────────────────────────

def _require_ceo_key(
    x_ceo_key: str | None = Header(default=None, alias="X-CEO-Key"),
) -> None:
    if not x_ceo_key or x_ceo_key != settings.ceo_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-CEO-Key header",
        )


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class InviteRequest(BaseModel):
    org_id: UUID
    inviter_user_id: UUID
    email: EmailStr
    role: str = "member"


class CreateOrgRequest(BaseModel):
    owner_user_id: UUID
    name: str
    slug: str


class RoleUpdatePayload(BaseModel):
    role: str
    org_id: UUID
    requester_user_id: UUID


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_org_or_404(db: Session, org_id: UUID) -> Organization:
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    return org


def _get_member_or_404(db: Session, member_id: UUID) -> OrgMember:
    m = db.get(OrgMember, member_id)
    if m is None:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    return m


async def _send_invite_email(
    to_email: str, invite_url: str, org_name: str, inviter_email: str
) -> None:
    """Send invitation email via SendGrid. No-op if key is not configured."""
    if not settings.sendgrid_api_key:
        logger.warning("SendGrid not configured — invite email not sent to %s", to_email)
        return

    body = {
        "personalizations": [{
            "to": [{"email": to_email}],
            "subject": f"Te invitaron a unirte a {org_name} en lokigi",
        }],
        "from": {"email": settings.sendgrid_from_email, "name": "lokigi"},
        "content": [{
            "type": "text/html",
            "value": (
                f"<p>Hola,</p>"
                f"<p><strong>{inviter_email}</strong> te invitó a unirte a "
                f"<strong>{org_name}</strong> como miembro de su equipo en lokigi.</p>"
                f"<p><a href='{invite_url}' style='background:#4f46e5;color:white;"
                f"padding:10px 20px;border-radius:8px;text-decoration:none;display:inline-block;'>"
                f"Aceptar invitación</a></p>"
                f"<p style='color:#6b7280;font-size:12px;'>Este enlace expira en {INVITE_TTL_HOURS} horas.</p>"
            ),
        }],
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=body,
                headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
            )
            resp.raise_for_status()
    except Exception as exc:
        logger.error("SendGrid send failed for %s: %s", to_email, exc)


def _build_member_rows(db: Session, org_id: UUID) -> list[dict]:
    members = db.scalars(
        select(OrgMember)
        .where(OrgMember.org_id == org_id, OrgMember.status != "deactivated")
        .order_by(OrgMember.created_at)
    ).all()
    rows = []
    for m in members:
        user = db.get(User, m.user_id) if m.user_id else None
        rows.append({
            "id": str(m.id),
            "user_id": str(m.user_id) if m.user_id else None,
            "email": m.email,
            "name": user.email if user else m.email,
            "role": m.role,
            "status": m.status,
            "joined_at": m.joined_at.strftime("%Y-%m-%d") if m.joined_at else None,
        })
    return rows


# ── HTML: Panel A — Member Management ────────────────────────────────────────

@router.get("/admin/members", response_class=HTMLResponse)
def admin_members_panel(
    request: Request,
    user_id: UUID = Query(...),
    org_id: UUID = Query(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    org = _get_org_or_404(db, org_id)

    # Resolve requester's role (they must be a member to view this panel)
    requester = db.scalar(
        select(OrgMember).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == user_id,
            OrgMember.status == "active",
        )
    )
    if requester is None:
        raise HTTPException(403, "No tienes acceso a este panel")

    member_rows = _build_member_rows(db, org_id)
    all_roles = [r for r in ROLE_TIER if r != "owner"]  # owner not assignable via UI

    return templates.TemplateResponse(
        "admin_members.html",
        {
            "request": request,
            "org": {"id": str(org.id), "name": org.name, "status": org.status},
            "user_id": str(user_id),
            "org_id": str(org_id),
            "requester_role": requester.role,
            "requester_tier": ROLE_TIER.get(requester.role, 0),
            "members": member_rows,
            "all_roles": all_roles,
            "role_permissions": {r: sorted(p) for r, p in ROLE_PERMISSIONS.items()},
            "can_invite": "manage_members" in ROLE_PERMISSIONS.get(requester.role, set()),
        },
    )


@router.get("/admin/members/accept", response_class=HTMLResponse)
def accept_invite(
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Claim an invite token — links user_id to the pending OrgMember row."""
    member = db.scalar(
        select(OrgMember).where(
            OrgMember.invite_token == token,
            OrgMember.status == "invited",
        )
    )
    if member is None:
        raise HTTPException(400, "Token de invitación inválido o expirado")
    if member.invite_expires_at and member.invite_expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "El enlace de invitación ha expirado. Solicita uno nuevo.")

    # Mark as active; caller may link user_id via a separate auth flow
    member.status = "active"
    member.joined_at = datetime.utcnow()
    member.invite_token = None
    db.commit()

    return RedirectResponse(
        url=f"/admin/members?org_id={member.org_id}",
        status_code=302,
    )


# ── API: Create organization ──────────────────────────────────────────────────

@router.post("/api/v1/admin/org", status_code=201)
def create_org(payload: CreateOrgRequest, db: Session = Depends(get_db)) -> dict:
    slug = payload.slug.lower().replace(" ", "-")
    if db.scalar(select(Organization).where(Organization.slug == slug)):
        raise HTTPException(409, "Ya existe una organización con ese slug")

    org = Organization(
        name=payload.name,
        slug=slug,
        owner_user_id=payload.owner_user_id,
        status="active",
    )
    db.add(org)
    db.flush()

    # Auto-add owner as member with owner role
    owner = OrgMember(
        org_id=org.id,
        user_id=payload.owner_user_id,
        email="",  # filled below
        role="owner",
        status="active",
        joined_at=datetime.utcnow(),
    )
    # Look up email
    user = db.get(User, payload.owner_user_id)
    if user:
        owner.email = user.email
    db.add(owner)
    db.commit()

    return {"org_id": str(org.id), "slug": org.slug, "message": "Organización creada"}


# ── API: Invite member ────────────────────────────────────────────────────────

@router.post("/api/v1/admin/members/invite")
async def invite_member(
    payload: InviteRequest,
    db: Session = Depends(get_db),
) -> dict:
    org = _get_org_or_404(db, payload.org_id)

    # RBAC: inviter must be admin or owner
    inviter = db.scalar(
        select(OrgMember).where(
            OrgMember.org_id == payload.org_id,
            OrgMember.user_id == payload.inviter_user_id,
            OrgMember.status == "active",
        )
    )
    if inviter is None or "manage_members" not in ROLE_PERMISSIONS.get(inviter.role, set()):
        raise HTTPException(403, "No tienes permiso para invitar miembros")

    # Cannot assign a role equal to or higher than own role
    if ROLE_TIER.get(payload.role, 0) >= ROLE_TIER.get(inviter.role, 0):
        raise HTTPException(
            422,
            detail={
                "code": "ROLE_ESCALATION",
                "message": (
                    f"No puedes asignar el rol '{payload.role}' "
                    f"(tu rol es '{inviter.role}')."
                ),
            },
        )

    # Check if already a member
    existing = db.scalar(
        select(OrgMember).where(
            OrgMember.org_id == payload.org_id,
            OrgMember.email == payload.email,
        )
    )
    if existing and existing.status == "active":
        raise HTTPException(409, "Ese usuario ya es miembro de esta organización")

    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=INVITE_TTL_HOURS)

    if existing:
        # Re-send invite
        existing.role = payload.role
        existing.invite_token = token
        existing.invite_expires_at = expires
        existing.status = "invited"
        db.commit()
        member = existing
    else:
        member = OrgMember(
            org_id=payload.org_id,
            email=payload.email,
            role=payload.role,
            status="invited",
            invite_token=token,
            invite_expires_at=expires,
            invited_by_user_id=payload.inviter_user_id,
        )
        db.add(member)
        db.commit()

    invite_url = f"https://{settings.app_domain}/admin/members/accept?token={token}"
    inviter_user = db.get(User, payload.inviter_user_id)
    inviter_email = inviter_user.email if inviter_user else "Un administrador"

    await _send_invite_email(payload.email, invite_url, org.name, inviter_email)

    return {
        "member_id": str(member.id),
        "email": payload.email,
        "role": payload.role,
        "invite_url": invite_url,
        "expires_at": expires.isoformat(),
        "message": f"Invitación enviada a {payload.email}",
    }


# ── API: HTMX role update ─────────────────────────────────────────────────────

@router.patch("/api/v1/admin/members/{member_id}/role", response_class=HTMLResponse)
def update_member_role(
    member_id: UUID,
    payload: RoleUpdatePayload,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """HTMX endpoint — returns an updated <tr> row fragment."""
    member = _get_member_or_404(db, member_id)

    # Verify requester is a member with manage_members permission
    requester = db.scalar(
        select(OrgMember).where(
            OrgMember.org_id == payload.org_id,
            OrgMember.user_id == payload.requester_user_id,
            OrgMember.status == "active",
        )
    )
    if requester is None or "manage_members" not in ROLE_PERMISSIONS.get(requester.role, set()):
        return HTMLResponse(
            content=_error_row("No tienes permiso para cambiar roles."),
            status_code=403,
        )

    if payload.role not in ROLE_TIER:
        return HTMLResponse(
            content=_error_row(f"Rol '{payload.role}' no válido."),
            status_code=422,
        )

    # Role escalation guard
    if ROLE_TIER.get(payload.role, 0) >= ROLE_TIER.get(requester.role, 0):
        return HTMLResponse(
            content=_error_row(
                f"No puedes asignar el rol '{payload.role}' (tu rol es '{requester.role}')."
            ),
            status_code=422,
        )

    # Cannot demote an owner
    if member.role == "owner":
        return HTMLResponse(
            content=_error_row("No se puede cambiar el rol del propietario de la organización."),
            status_code=422,
        )

    member.role = payload.role
    member.updated_at = datetime.utcnow()
    db.commit()

    # Return an HTMX-compatible row fragment
    user = db.get(User, member.user_id) if member.user_id else None
    assignable_roles = [r for r in ROLE_TIER if r != "owner"]
    return HTMLResponse(content=_member_row_html(member, user, assignable_roles, payload.org_id, payload.requester_user_id))


# ── API: Remove member ────────────────────────────────────────────────────────

@router.delete("/api/v1/admin/members/{member_id}", response_class=HTMLResponse)
def remove_member(
    member_id: UUID,
    org_id: UUID = Query(...),
    requester_user_id: UUID = Query(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """HTMX endpoint — deletes row on success (returns empty 200)."""
    member = _get_member_or_404(db, member_id)

    requester = db.scalar(
        select(OrgMember).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == requester_user_id,
            OrgMember.status == "active",
        )
    )
    if requester is None or "manage_members" not in ROLE_PERMISSIONS.get(requester.role, set()):
        return HTMLResponse(content=_error_row("No tienes permiso para eliminar miembros."), status_code=403)

    if member.role == "owner":
        return HTMLResponse(content=_error_row("No se puede eliminar al propietario."), status_code=422)

    member.status = "deactivated"
    db.commit()
    # Return empty string — HTMX swap='outerHTML' will remove the row
    return HTMLResponse(content="", status_code=200)


# ── HTMX fragment helpers ─────────────────────────────────────────────────────

def _error_row(message: str) -> str:
    """Single-row error fragment for HTMX out-of-band swap."""
    return (
        f'<tr id="htmx-error-toast" hx-swap-oob="true">'
        f'<td colspan="5" class="px-4 py-3 text-sm text-red-700 bg-red-50 rounded">'
        f'⚠ {message}</td></tr>'
    )


def _member_row_html(
    member: OrgMember,
    user: User | None,
    assignable_roles: list[str],
    org_id: UUID,
    requester_user_id: UUID,
) -> str:
    name = user.email if user else member.email
    status_badge = (
        '<span class="badge badge-active">Activo</span>'
        if member.status == "active"
        else '<span class="badge badge-neutral">Invitado</span>'
    )
    role_opts = "".join(
        f'<option value="{r}" {"selected" if r == member.role else ""}>{r.capitalize()}</option>'
        for r in assignable_roles
    )
    return f"""
<tr id="member-row-{member.id}"
    hx-target="#member-row-{member.id}"
    hx-swap="outerHTML">
  <td class="px-4 py-3 text-sm font-medium">{name}</td>
  <td class="px-4 py-3">{status_badge}</td>
  <td class="px-4 py-3">
    <form hx-patch="/api/v1/admin/members/{member.id}/role"
          hx-target="#member-row-{member.id}"
          hx-swap="outerHTML"
          hx-vals='{{"org_id":"{org_id}","requester_user_id":"{requester_user_id}"}}'
          class="inline">
      <select name="role"
              onchange="this.form.requestSubmit()"
              class="text-sm border border-gray-200 rounded px-2 py-1 bg-white focus:ring-2 focus:ring-indigo-500">
        {role_opts}
      </select>
    </form>
  </td>
  <td class="px-4 py-3 text-xs text-gray-400">
    {member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Pendiente"}
  </td>
  <td class="px-4 py-3 text-right">
    <button
      hx-delete="/api/v1/admin/members/{member.id}?org_id={org_id}&requester_user_id={requester_user_id}"
      hx-target="#member-row-{member.id}"
      hx-swap="outerHTML"
      hx-confirm="¿Eliminar a {name} del equipo?"
      class="text-xs text-red-500 hover:underline"
    >Eliminar</button>
  </td>
</tr>
"""


# ── CEO KPIs ──────────────────────────────────────────────────────────────────

@router.get(
    "/api/v1/ceo/subscription-kpis",
    summary="CEO: Expansion revenue, user-to-location ratio, churn by plan",
    dependencies=[Depends(_require_ceo_key)],
)
def subscription_kpis(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return three strategic KPIs:

    1. avg_expansion_revenue_usd — average net revenue per plan upgrade
    2. user_to_location_ratio    — org members per connected Google location
    3. churn_by_plan             — churn event count grouped by subscription plan
    """
    # ── 1. Average expansion revenue (from ProrationCredit upgrades) ─────────
    from app.models import ProrationCredit

    upgrade_rows = db.execute(
        select(
            func.avg(ProrationCredit.net_cents).label("avg_net"),
            func.count(ProrationCredit.id).label("cnt"),
            func.sum(ProrationCredit.net_cents).label("total_net"),
        ).where(
            ProrationCredit.net_cents > 0,  # positive net = upgrade charge
            ProrationCredit.status.in_(["applied", "pending"]),
        )
    ).one()

    avg_expansion_usd = round((upgrade_rows.avg_net or 0) / 100, 2)
    total_expansion_usd = round((upgrade_rows.total_net or 0) / 100, 2)
    upgrade_count = upgrade_rows.cnt or 0

    # ── 2. User-to-location ratio ─────────────────────────────────────────────
    total_members = db.scalar(
        select(func.count(OrgMember.id)).where(OrgMember.status == "active")
    ) or 0
    total_locations = db.scalar(
        select(func.count(GoogleConnection.id))
    ) or 0
    user_to_location_ratio = (
        round(total_members / total_locations, 2) if total_locations > 0 else None
    )

    # ── 3. Churn by plan ──────────────────────────────────────────────────────
    # Join LifecycleEvent (event_type='churned') with SubscriptionProfile at churn time
    churn_by_plan_rows = db.execute(
        select(
            SubscriptionProfile.subscription_plan.label("plan"),
            func.count(LifecycleEvent.id).label("churn_count"),
        )
        .join(SubscriptionProfile, SubscriptionProfile.user_id == LifecycleEvent.user_id)
        .where(LifecycleEvent.event_type == "churned")
        .group_by(SubscriptionProfile.subscription_plan)
        .order_by(func.count(LifecycleEvent.id).desc())
    ).all()

    churn_by_plan = [
        {"plan": row.plan, "churn_count": row.churn_count}
        for row in churn_by_plan_rows
    ]

    # Identify highest-churn plan
    highest_churn_plan = churn_by_plan[0]["plan"] if churn_by_plan else None

    return {
        "expansion_revenue": {
            "avg_per_upgrade_usd": avg_expansion_usd,
            "total_usd": total_expansion_usd,
            "upgrade_count": upgrade_count,
            "label": "Avg Expansion Revenue",
            "description": "Ingreso promedio adicional por upgrade de plan (prorrateo positivo).",
        },
        "user_to_location_ratio": {
            "ratio": user_to_location_ratio,
            "total_active_members": total_members,
            "total_locations": total_locations,
            "label": "User-to-Location Ratio",
            "description": "Empleados activos por ubicación conectada. >3 sugiere candidato Enterprise.",
        },
        "churn_by_plan": {
            "breakdown": churn_by_plan,
            "highest_churn_plan": highest_churn_plan,
            "label": "Churn por Plan",
            "description": "Número de eventos de churn agrupados por plan de suscripción.",
        },
    }


# ── Admin: trigger manual expiry check ───────────────────────────────────────

@router.post(
    "/api/v1/admin/subscriptions/run-expiry",
    dependencies=[Depends(_require_ceo_key)],
    summary="Manually trigger daily subscription expiry check",
)
def run_expiry_check(db: Session = Depends(get_db)) -> dict:
    from app.subscription_manager import run_daily_expiry_check
    result = run_daily_expiry_check(db)
    return result
