"""routes/crm_routes.py — Executive CRM endpoints.

All routes require X-CEO-Key header (same guard as the CEO Command Center).

Endpoints
─────────
GET  /api/v1/crm/customers          → paginated customer list with health scores
GET  /api/v1/crm/customers/{user_id} → single customer detail
PATCH /api/v1/crm/customers/{user_id}/notes  → update CEO notes
POST /api/v1/crm/customers/{user_id}/recompute  → recompute health score on demand
POST /api/v1/crm/customers/{user_id}/support-email  → send pre-designed support email
GET  /crm/dashboard                 → Jinja2 HTML CRM table
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.customer_health_service import compute_health_score, record_user_session
from app.database import get_db
from app.models import (
    CustomerInsight,
    GoogleConnection,
    SubscriptionProfile,
    User,
)

router = APIRouter(tags=["crm"])
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Auth guard (shared with CEO Command Center)
# ──────────────────────────────────────────────────────────────────────────────


def _require_ceo_key(x_ceo_key: str | None = Header(default=None, alias="X-CEO-Key")) -> None:
    if not x_ceo_key or x_ceo_key != settings.ceo_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-CEO-Key header")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_BUCKET_LABELS = {
    "upsell_candidate": "Candidato a Upsell",
    "healthy": "Saludable",
    "churn_risk": "Riesgo de Churn",
}


def _build_customer_row(user: User, insight: CustomerInsight | None, conn: GoogleConnection | None, sub: SubscriptionProfile | None) -> dict[str, Any]:
    return {
        "user_id": str(user.id),
        "email": user.email,
        "business_name": conn.business_name if conn else None,
        "plan": sub.subscription_plan if sub else "starter",
        "plan_status": sub.subscription_status if sub else "unknown",
        "health_score": insight.health_score if insight else None,
        "bucket": insight.bucket if insight else "unknown",
        "bucket_label": _BUCKET_LABELS.get(insight.bucket if insight else "", "—"),
        "login_score": insight.login_score if insight else None,
        "response_rate_score": insight.response_rate_score if insight else None,
        "ranking_score": insight.ranking_score if insight else None,
        "response_rate_pct": float(insight.response_rate_pct) if insight and insight.response_rate_pct is not None else None,
        "rank_delta": insight.rank_delta if insight else None,
        "days_since_last_activity": insight.days_since_last_activity if insight else None,
        "ceo_notes": insight.ceo_notes if insight else None,
        "support_email_sent_at": insight.support_email_sent_at.isoformat() if insight and insight.support_email_sent_at else None,
        "computed_at": insight.computed_at.isoformat() if insight and insight.computed_at else None,
        "member_since": user.created_at.isoformat(),
    }


def _fetch_rows(
    db: Session,
    *,
    bucket: str | None,
    plan: str | None,
    search: str | None,
    offset: int,
    limit: int,
) -> tuple[list[dict], int]:
    """Query and build all customer rows applying filters."""
    q = select(User)
    if search:
        term = f"%{search}%"
        q = q.join(GoogleConnection, GoogleConnection.user_id == User.id, isouter=True).where(
            or_(User.email.ilike(term), GoogleConnection.business_name.ilike(term))
        )

    users = db.scalars(q).all()

    rows = []
    for user in users:
        conn = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user.id))
        sub = db.scalar(select(SubscriptionProfile).where(SubscriptionProfile.user_id == user.id))
        insight = db.scalar(select(CustomerInsight).where(CustomerInsight.user_id == user.id))

        # Apply filters that can't easily be done with JOIN on optional tables
        if bucket and (insight is None or insight.bucket != bucket):
            continue
        if plan and (sub is None or sub.subscription_plan != plan):
            continue

        rows.append(_build_customer_row(user, insight, conn, sub))

    total = len(rows)
    # Sort: churn_risk first, then by health_score asc (worst first)
    rows.sort(key=lambda r: (
        0 if r["bucket"] == "churn_risk" else (2 if r["bucket"] == "upsell_candidate" else 1),
        r["health_score"] if r["health_score"] is not None else 50,
    ))
    return rows[offset: offset + limit], total


# ──────────────────────────────────────────────────────────────────────────────
# JSON API
# ──────────────────────────────────────────────────────────────────────────────


@router.get(
    "/api/v1/crm/customers",
    summary="List customers with health scores (filterable)",
    dependencies=[Depends(_require_ceo_key)],
)
def list_customers(
    db: Session = Depends(get_db),
    bucket: str | None = Query(default=None, description="upsell_candidate | healthy | churn_risk"),
    plan: str | None = Query(default=None, description="starter | growth | enterprise"),
    search: str | None = Query(default=None, description="Search by business name or email"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    rows, total = _fetch_rows(db, bucket=bucket, plan=plan, search=search, offset=offset, limit=limit)
    return {"total": total, "offset": offset, "limit": limit, "customers": rows}


@router.get(
    "/api/v1/crm/customers/{user_id}",
    summary="Get single customer health detail",
    dependencies=[Depends(_require_ceo_key)],
)
def get_customer(user_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    conn = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    sub = db.scalar(select(SubscriptionProfile).where(SubscriptionProfile.user_id == user_id))
    insight = db.scalar(select(CustomerInsight).where(CustomerInsight.user_id == user_id))
    return _build_customer_row(user, insight, conn, sub)


class NotesPayload(BaseModel):
    notes: str


@router.patch(
    "/api/v1/crm/customers/{user_id}/notes",
    summary="Update CEO notes for a customer",
    dependencies=[Depends(_require_ceo_key)],
)
def update_notes(user_id: UUID, payload: NotesPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    insight = db.scalar(select(CustomerInsight).where(CustomerInsight.user_id == user_id))
    if not insight:
        insight = compute_health_score(db, user_id)
    insight.ceo_notes = payload.notes[:2000]
    insight.updated_at = datetime.now(tz=timezone.utc)
    db.commit()
    return {"ok": True, "notes": insight.ceo_notes}


@router.post(
    "/api/v1/crm/customers/{user_id}/recompute",
    summary="Force-recompute health score for a customer",
    dependencies=[Depends(_require_ceo_key)],
)
def recompute_score(user_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    insight = compute_health_score(db, user_id)
    conn = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    sub = db.scalar(select(SubscriptionProfile).where(SubscriptionProfile.user_id == user_id))
    return _build_customer_row(user, insight, conn, sub)


# ──────────────────────────────────────────────────────────────────────────────
# Support email action
# ──────────────────────────────────────────────────────────────────────────────

_EMAIL_TEMPLATES = {
    "churn_risk": {
        "subject": "¿Podemos ayudarte? Tu opinión es muy importante para nosotros",
        "body_html": """\
<p>Hola {business_name},</p>
<p>Hemos notado que últimamente no has estado tan activo en tu cuenta de <strong>lokigi</strong>
y nos gustaría saber cómo podemos mejorar tu experiencia.</p>
<p>Nuestro equipo está disponible para una sesión de onboarding personalizada o para resolver
cualquier duda que tengas.</p>
<p><a href="https://{domain}/support?user={user_id}" style="background:#6366f1;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;">Reservar una llamada gratis</a></p>
<p>¡Estamos aquí para ayudarte!</p>
<p>El equipo de lokigi</p>""",
    },
    "upsell_candidate": {
        "subject": "🚀 Tus resultados son excelentes — descubre el Plan Growth",
        "body_html": """\
<p>Hola {business_name},</p>
<p>¡Enhorabuena! Has estado respondiendo a tus reseñas con una tasa de respuesta excepcional
y tu posicionamiento en Google Maps está mejorando notablemente.</p>
<p>Creemos que estás listo para dar el siguiente paso con el <strong>Plan Growth</strong>:
monitorización de competidores, radar de sentimiento, optimización SEO de fotos y mucho más.</p>
<p><a href="https://{domain}/upgrade?user={user_id}" style="background:#10b981;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;">Ver Plan Growth</a></p>
<p>El equipo de lokigi</p>""",
    },
    "healthy": {
        "subject": "Gracias por confiar en lokigi",
        "body_html": """\
<p>Hola {business_name},</p>
<p>Queremos agradecerte por ser un cliente activo de lokigi. Estás haciendo un gran trabajo
gestionando tu reputación online.</p>
<p>¿Hay algo en lo que podamos mejorar tu experiencia? Escríbenos cuando quieras.</p>
<p>El equipo de lokigi</p>""",
    },
}


def _send_sendgrid_email(to_email: str, subject: str, body_html: str) -> bool:
    if not settings.sendgrid_api_key:
        logger.warning("SendGrid not configured — email not sent to %s", to_email)
        return False
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": settings.sendgrid_from_email},
        "subject": subject,
        "content": [{"type": "text/html", "value": body_html}],
    }
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
            )
        return resp.status_code in (200, 202)
    except Exception as exc:
        logger.warning("SendGrid send failed: %s", exc)
        return False


@router.post(
    "/api/v1/crm/customers/{user_id}/support-email",
    summary="Send a pre-designed support/upsell email to a customer",
    dependencies=[Depends(_require_ceo_key)],
)
def send_support_email(
    user_id: UUID,
    db: Session = Depends(get_db),
    template: str = Query(default="auto", description="churn_risk | upsell_candidate | healthy | auto"),
) -> dict[str, Any]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    conn = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    insight = db.scalar(select(CustomerInsight).where(CustomerInsight.user_id == user_id))
    if not insight:
        insight = compute_health_score(db, user_id)

    # Determine template
    tpl_key = template if template in _EMAIL_TEMPLATES else insight.bucket
    if tpl_key not in _EMAIL_TEMPLATES:
        tpl_key = "healthy"
    tpl = _EMAIL_TEMPLATES[tpl_key]

    business_name = (conn.business_name if conn else None) or user.email.split("@")[0]
    body_html = tpl["body_html"].format(
        business_name=business_name,
        domain=settings.app_domain,
        user_id=str(user_id),
    )

    sent = _send_sendgrid_email(user.email, tpl["subject"], body_html)

    if sent:
        insight.support_email_sent_at = datetime.now(tz=timezone.utc)
        db.commit()

    return {
        "ok": True,
        "sent": sent,
        "template_used": tpl_key,
        "to": user.email,
        "subject": tpl["subject"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# HTML Dashboard
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/crm/dashboard", response_class=HTMLResponse, summary="Executive CRM Dashboard")
def crm_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    x_ceo_key: str | None = Header(default=None, alias="X-CEO-Key"),
    bucket: str | None = Query(default=None),
    plan: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    qkey = request.query_params.get("key")
    key_to_check = x_ceo_key or qkey
    if not key_to_check or key_to_check != settings.ceo_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    rows, total = _fetch_rows(db, bucket=bucket, plan=plan, search=search, offset=0, limit=200)
    return templates.TemplateResponse(
        "crm_dashboard.html",
        {
            "request": request,
            "customers": rows,
            "total": total,
            "ceo_key": key_to_check,
            "active_bucket": bucket or "",
            "active_plan": plan or "",
            "search": search or "",
        },
    )
