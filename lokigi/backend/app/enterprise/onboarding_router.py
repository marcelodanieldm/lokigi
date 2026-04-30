"""
backend/app/enterprise/onboarding_router.py
============================================
Enterprise Onboarding API — 3-phase wizard.

Phase 1 — Identity / White-Label Setup
  POST   /enterprise/onboarding/setup           Create org + initial branding
  PATCH  /enterprise/onboarding/branding/{id}   Update colors / logos
  PATCH  /enterprise/onboarding/smtp/{id}        Store SMTP credentials (encrypted)

Phase 2 — Structure / Bulk Import
  POST   /enterprise/onboarding/locations/preview   Validate CSV/Excel (dry-run)
  POST   /enterprise/onboarding/locations/import    Commit locations + fire Celery

Phase 3 — Governance
  POST   /enterprise/onboarding/invite/bulk          Bulk invite users by email
  GET    /enterprise/onboarding/status/{org_id}      Overall onboarding progress

Security
--------
All write endpoints require `RoleChecker(["superadmin"])`.
File uploads are validated for content-type and capped at 10 MB (logo) / 20 MB (CSV).
SMTP passwords are encrypted with Fernet before storage.
"""
from __future__ import annotations

import io
import logging
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.enterprise.audit_log import AuditAction, AuditService
from app.enterprise.bulk_import_service import BulkImportService, ImportPreview
from app.enterprise.multi_tenancy import Organization, OrgMembership
from app.enterprise.rbac_auth import RoleChecker
from app.models import User

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

_MAX_LOGO_BYTES    = 10 * 1024 * 1024   # 10 MB
_MAX_CSV_BYTES     = 20 * 1024 * 1024   # 20 MB
_ALLOWED_IMG_TYPES = {"image/png", "image/jpeg", "image/svg+xml", "image/webp"}
_ALLOWED_CSV_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

_ASSETS_DIR = Path(getattr(settings, "assets_upload_dir", "assets/uploads"))

# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class OrgCreatePayload(BaseModel):
    name: str
    slug: str
    domain: str | None = None
    primary_color: str = "#7c3aed"
    secondary_color: str = "#4f46e5"
    font_family: str = "Inter, sans-serif"
    agency_name: str | None = None
    agency_email: str | None = None

    @validator("slug")
    def slug_format(cls, v: str) -> str:
        import re
        v = v.strip().lower()
        if not re.fullmatch(r"[a-z0-9\-]{3,64}", v):
            raise ValueError("slug must be 3-64 chars, only lowercase letters, digits and hyphens")
        return v

    @validator("primary_color", "secondary_color")
    def valid_hex(cls, v: str) -> str:
        import re
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", v.strip()):
            raise ValueError("Color must be a 6-digit hex code, e.g. #7c3aed")
        return v.strip().lower()


class BrandingUpdatePayload(BaseModel):
    primary_color: str | None = None
    secondary_color: str | None = None
    font_family: str | None = None
    agency_name: str | None = None
    agency_email: str | None = None
    domain: str | None = None
    hide_lokigi_brand: bool | None = None


class SmtpPayload(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str          # plaintext in transit (HTTPS-only); encrypted at rest
    smtp_use_tls: bool = True


class BulkInviteItem(BaseModel):
    email: EmailStr
    role: str

    @validator("role")
    def valid_role(cls, v: str) -> str:
        valid = {"superadmin", "network_manager", "store_manager", "store_staff"}
        if v not in valid:
            raise ValueError(f"role must be one of: {', '.join(sorted(valid))}")
        return v


class BulkInvitePayload(BaseModel):
    org_id: uuid.UUID
    invites: list[BulkInviteItem]

    @validator("invites")
    def limit_size(cls, v):
        if len(v) > 200:
            raise ValueError("Maximum 200 invites per request")
        return v


# ─── Router ───────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/enterprise/onboarding", tags=["Enterprise Onboarding"])

_require_superadmin = Depends(RoleChecker(["superadmin"]))


# ── Phase 1a: Create organization ─────────────────────────────────────────────

@router.post("/setup", status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrgCreatePayload,
    request: Request,
    db: Session = Depends(get_db),
    _: None = _require_superadmin,
) -> dict:
    """
    Create a new Organization (tenant).  The calling user becomes the SuperAdmin.
    Sets onboarding_step = 1 (branding pending).
    """
    existing = db.scalars(
        select(Organization).where(Organization.slug == payload.slug)
    ).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Slug already taken")

    org = Organization(
        slug=payload.slug,
        name=payload.name,
        domain=payload.domain,
        primary_color=payload.primary_color,
        secondary_color=payload.secondary_color,
        font_family=payload.font_family,
        agency_name=payload.agency_name or payload.name,
        agency_email=payload.agency_email,
        onboarding_step=1,
    )
    db.add(org)
    db.flush()  # get org.id

    # Auto-enroll the calling user as SuperAdmin
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        membership = OrgMembership(
            user_id=user_id,
            org_id=org.id,
            role="superadmin",
        )
        db.add(membership)

    AuditService.log(
        db,
        org_id=org.id,
        action=AuditAction.ORG_CREATED,
        actor_id=user_id,
        actor_role="superadmin",
        resource_type="organization",
        resource_id=str(org.id),
        details={"slug": org.slug, "name": org.name},
        request=request,
    )
    db.commit()

    return {
        "org_id": str(org.id),
        "slug": org.slug,
        "name": org.name,
        "onboarding_step": 1,
        "next": f"/enterprise/onboarding/branding/{org.id}",
    }


# ── Phase 1b: Upload logo / isotipo ───────────────────────────────────────────

@router.post("/branding/{org_id}/logo")
async def upload_logo(
    org_id: uuid.UUID,
    request: Request,
    logo: UploadFile = File(..., description="Primary logo (PNG/JPG/SVG/WEBP, max 10 MB)"),
    isotipo: UploadFile | None = File(None, description="Isotipo / icon (optional)"),
    db: Session = Depends(get_db),
    _: None = _require_superadmin,
) -> dict:
    """Upload logo and optional isotipo.  Files are saved to the assets directory."""
    org = _get_org_or_404(org_id, db)

    logo_url    = await _save_upload(org_id, logo,    "logo",    _MAX_LOGO_BYTES)
    isotipo_url = await _save_upload(org_id, isotipo, "isotipo", _MAX_LOGO_BYTES) if isotipo else org.isotipo_url

    org.logo_url    = logo_url
    org.isotipo_url = isotipo_url
    db.commit()

    return {"logo_url": logo_url, "isotipo_url": isotipo_url}


# ── Phase 1b: Update branding variables ───────────────────────────────────────

@router.patch("/branding/{org_id}")
async def update_branding(
    org_id: uuid.UUID,
    payload: BrandingUpdatePayload,
    request: Request,
    db: Session = Depends(get_db),
    _: None = _require_superadmin,
) -> dict:
    """Update CSS variables and identity fields.  Only supplied fields are changed."""
    org = _get_org_or_404(org_id, db)

    if payload.primary_color   is not None: org.primary_color   = payload.primary_color
    if payload.secondary_color is not None: org.secondary_color = payload.secondary_color
    if payload.font_family     is not None: org.font_family     = payload.font_family
    if payload.agency_name     is not None: org.agency_name     = payload.agency_name
    if payload.agency_email    is not None: org.agency_email    = payload.agency_email
    if payload.domain          is not None: org.domain          = payload.domain
    if payload.hide_lokigi_brand is not None: org.hide_lokigi_brand = payload.hide_lokigi_brand

    # Advance onboarding step if still at 1
    if org.onboarding_step == 1:
        org.onboarding_step = 2   # → ready for bulk import

    AuditService.log(
        db,
        org_id=org.id,
        action=AuditAction.ORG_WHITE_LABEL_UPDATED,
        actor_id=getattr(request.state, "user_id", None),
        actor_role="superadmin",
        resource_type="organization",
        resource_id=str(org.id),
        details=payload.model_dump(exclude_none=True),
        request=request,
    )
    db.commit()
    return {"status": "ok", "onboarding_step": org.onboarding_step}


# ── Phase 1c: SMTP configuration ─────────────────────────────────────────────

@router.patch("/smtp/{org_id}")
async def configure_smtp(
    org_id: uuid.UUID,
    payload: SmtpPayload,
    request: Request,
    db: Session = Depends(get_db),
    _: None = _require_superadmin,
) -> dict:
    """
    Store SMTP credentials (password encrypted with Fernet).
    Used to send org-branded invitations and report emails.
    """
    org = _get_org_or_404(org_id, db)

    enc_password = _encrypt(payload.smtp_password)

    org.smtp_host         = payload.smtp_host
    org.smtp_port         = payload.smtp_port
    org.smtp_user         = payload.smtp_user
    org.smtp_password_enc = enc_password
    org.smtp_use_tls      = payload.smtp_use_tls

    AuditService.log(
        db,
        org_id=org.id,
        action=AuditAction.ORG_SMTP_CONFIGURED,
        actor_id=getattr(request.state, "user_id", None),
        actor_role="superadmin",
        resource_type="organization",
        resource_id=str(org.id),
        details={"smtp_host": payload.smtp_host, "smtp_user": payload.smtp_user},
        request=request,
    )
    db.commit()
    return {"status": "ok", "smtp_host": org.smtp_host}


# ── Phase 2a: Preview bulk import ─────────────────────────────────────────────

@router.post("/locations/preview")
async def preview_locations_import(
    org_id: Annotated[uuid.UUID, Form()],
    file: UploadFile = File(..., description="CSV or Excel with place_id / address columns"),
    db: Session = Depends(get_db),
    _: None = _require_superadmin,
) -> ImportPreview:
    """
    Dry-run: parse and validate the uploaded file, return preview stats.
    No data is written to the DB.
    """
    _validate_csv_upload(file)
    raw = await file.read()
    if len(raw) > _MAX_CSV_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large (max 20 MB)")

    preview = BulkImportService.preview(io.BytesIO(raw), file.filename or "upload.csv")
    return preview


# ── Phase 2b: Commit bulk import ──────────────────────────────────────────────

@router.post("/locations/import")
async def import_locations(
    org_id: Annotated[uuid.UUID, Form()],
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    request: Request = None,
    db: Session = Depends(get_db),
    _: None = _require_superadmin,
) -> dict:
    """
    Commit validated rows to `org_locations`.
    Fires a Celery scrape task for the entire batch.
    Advances onboarding_step → 3.
    """
    _validate_csv_upload(file)
    raw = await file.read()
    if len(raw) > _MAX_CSV_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large (max 20 MB)")

    org = _get_org_or_404(org_id, db)
    result = BulkImportService.commit(io.BytesIO(raw), file.filename or "upload.csv", org_id=org_id, db=db)

    if org.onboarding_step == 2:
        org.onboarding_step = 3

    AuditService.log(
        db,
        org_id=org.id,
        action=AuditAction.BULK_PUBLISH_TRIGGERED,
        actor_id=getattr(request.state, "user_id", None) if request else None,
        actor_role="superadmin",
        resource_type="org_location",
        resource_id=str(org_id),
        details={"inserted": result["inserted"], "skipped": result["skipped"]},
        request=request,
    )
    db.commit()

    # Fire Celery scrape job in the background (non-blocking)
    background_tasks.add_task(_trigger_bulk_scrape, org_id=str(org_id), location_ids=result["location_ids"])

    return {
        "inserted": result["inserted"],
        "skipped": result["skipped"],
        "total": result["total"],
        "onboarding_step": org.onboarding_step,
        "next": f"/enterprise/onboarding/invite/bulk",
    }


# ── Phase 3: Bulk invite ───────────────────────────────────────────────────────

@router.post("/invite/bulk")
async def bulk_invite(
    payload: BulkInvitePayload,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = _require_superadmin,
) -> dict:
    """
    Queue invitation emails for each address.
    Inserts pending UserOrgRole rows (no user_id yet — resolved on first login).
    Advances onboarding_step → 4 (complete).
    """
    from app.enterprise.rbac_models import Role, UserOrgRole

    org = _get_org_or_404(payload.org_id, db)

    # Resolve role IDs once
    roles_by_slug: dict[str, uuid.UUID] = {
        r.slug: r.id
        for r in db.scalars(select(Role)).all()
    }

    queued: list[str] = []
    skipped: list[str] = []

    for item in payload.invites:
        role_id = roles_by_slug.get(item.role)
        if not role_id:
            skipped.append(item.email)
            continue

        # Find or pre-register user
        user = db.scalars(select(User).where(User.email == item.email)).first()
        if user:
            # If user already has a role in this org, skip
            existing = db.scalars(
                select(UserOrgRole).where(
                    UserOrgRole.user_id == user.id,
                    UserOrgRole.org_id == payload.org_id,
                )
            ).first()
            if existing:
                skipped.append(item.email)
                continue
            actor_id = getattr(request.state, "user_id", None)
            uar = UserOrgRole(
                user_id=user.id,
                org_id=payload.org_id,
                role_id=role_id,
                invited_by=actor_id,
            )
            db.add(uar)

        queued.append(item.email)

        # Queue email in background (fire-and-forget)
        background_tasks.add_task(
            _send_invite_email,
            email=item.email,
            org_name=org.agency_name or org.name,
            role=item.role,
            org_smtp=_smtp_config(org),
        )

    if org.onboarding_step == 3 and queued:
        org.onboarding_step = 4   # onboarding complete

    AuditService.log(
        db,
        org_id=org.id,
        action=AuditAction.USER_INVITED,
        actor_id=getattr(request.state, "user_id", None),
        actor_role="superadmin",
        resource_type="user_invite_batch",
        resource_id=str(payload.org_id),
        details={"queued": len(queued), "skipped": len(skipped)},
        request=request,
    )
    db.commit()

    return {
        "queued": len(queued),
        "skipped": len(skipped),
        "onboarding_complete": org.onboarding_step == 4,
        "dashboard_url": f"/enterprise/dashboard/{payload.org_id}",
    }


# ── Status endpoint ───────────────────────────────────────────────────────────

@router.get("/status/{org_id}")
def onboarding_status(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: None = _require_superadmin,
) -> dict:
    """Return onboarding progress for the wizard UI."""
    org = _get_org_or_404(org_id, db)

    member_count = db.scalar(
        text("SELECT COUNT(*) FROM org_memberships WHERE org_id = :oid"),
        {"oid": str(org_id)},
    ) or 0
    location_count = db.scalar(
        text("SELECT COUNT(*) FROM org_locations WHERE org_id = :oid"),
        {"oid": str(org_id)},
    ) or 0

    steps = {
        1: {"label": "Identidad & Branding",   "complete": org.onboarding_step > 1},
        2: {"label": "Importación de Locales",  "complete": org.onboarding_step > 2},
        3: {"label": "Gobernanza & Roles",      "complete": org.onboarding_step > 3},
        4: {"label": "Dashboard en Vivo",       "complete": org.onboarding_step >= 4},
    }

    return {
        "org_id": str(org_id),
        "name": org.name,
        "onboarding_step": org.onboarding_step,
        "complete": org.onboarding_step >= 4,
        "steps": steps,
        "member_count": member_count,
        "location_count": location_count,
        "branding": {
            "primary_color":   org.primary_color,
            "secondary_color": org.secondary_color,
            "font_family":     org.font_family,
            "logo_url":        org.logo_url,
            "isotipo_url":     org.isotipo_url,
        },
        "smtp_configured": bool(org.smtp_host),
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_org_or_404(org_id: uuid.UUID, db: Session) -> Organization:
    org = db.scalars(select(Organization).where(Organization.id == org_id)).first()
    if not org:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


async def _save_upload(org_id: uuid.UUID, upload: UploadFile, kind: str, max_bytes: int) -> str:
    """Validate + save an image upload.  Returns the public URL path."""
    content_type = upload.content_type or mimetypes.guess_type(upload.filename or "")[0] or ""
    if content_type not in _ALLOWED_IMG_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported image type: {content_type}. Allowed: PNG, JPG, SVG, WEBP",
        )
    raw = await upload.read()
    if len(raw) > max_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"{kind} exceeds {max_bytes // 1024 // 1024} MB limit")

    ext       = Path(upload.filename or "logo.png").suffix or ".png"
    dest_dir  = _ASSETS_DIR / str(org_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / f"{kind}{ext}"

    dest_file.write_bytes(raw)
    return f"/assets/{org_id}/{kind}{ext}"


def _validate_csv_upload(file: UploadFile) -> None:
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if content_type not in _ALLOWED_CSV_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Expected CSV or Excel file, got: {content_type}",
        )


def _encrypt(plaintext: str) -> str:
    """Encrypt a string with Fernet (same key as oauth_token_encryption_key)."""
    from cryptography.fernet import Fernet
    key = settings.oauth_token_encryption_key
    if not key:
        logger.warning("oauth_token_encryption_key not set — SMTP password stored in plaintext")
        return plaintext
    return Fernet(key.encode()).encrypt(plaintext.encode()).decode()


def _smtp_config(org: Organization) -> dict | None:
    if not org.smtp_host:
        return None
    return {
        "host": org.smtp_host,
        "port": org.smtp_port,
        "user": org.smtp_user,
        "password_enc": org.smtp_password_enc,
        "use_tls": org.smtp_use_tls,
    }


def _trigger_bulk_scrape(org_id: str, location_ids: list[str]) -> None:
    """Fire-and-forget Celery task to scrape the imported locations."""
    try:
        from tasks.scraping import scrape_bulk_locations  # type: ignore[import]
        scrape_bulk_locations.delay(org_id=org_id, location_ids=location_ids)
    except Exception as exc:
        logger.warning("Could not queue bulk scrape task: %s", exc)


def _send_invite_email(email: str, org_name: str, role: str, org_smtp: dict | None) -> None:
    """Background task — sends a plain invitation email."""
    try:
        import smtplib, ssl
        from email.mime.text import MIMEText

        body = (
            f"Hola,\n\n"
            f"Has sido invitado a unirte a {org_name} en Lokigi Enterprise "
            f"con el rol: {role}.\n\n"
            f"Visita el portal para activar tu cuenta.\n\n"
            f"— El equipo de {org_name}"
        )
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = f"Invitación a {org_name} · Lokigi Enterprise"
        msg["From"]    = org_smtp["user"] if org_smtp else settings.sendgrid_from_email
        msg["To"]      = email

        if org_smtp:
            from cryptography.fernet import Fernet
            key = settings.oauth_token_encryption_key
            if key:
                pw = Fernet(key.encode()).decrypt(org_smtp["password_enc"].encode()).decode()
            else:
                pw = org_smtp["password_enc"]

            ctx = ssl.create_default_context()
            with smtplib.SMTP(org_smtp["host"], org_smtp["port"]) as s:
                if org_smtp["use_tls"]:
                    s.starttls(context=ctx)
                s.login(org_smtp["user"], pw)
                s.send_message(msg)
        else:
            # Fallback: SendGrid REST API if configured
            if settings.sendgrid_api_key:
                import sendgrid  # type: ignore[import]
                from sendgrid.helpers.mail import Mail  # type: ignore[import]
                sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
                mail = Mail(
                    from_email=settings.sendgrid_from_email,
                    to_emails=email,
                    subject=msg["Subject"],
                    plain_text_content=body,
                )
                sg.send(mail)
    except Exception as exc:
        logger.error("Invite email to %s failed: %s", email, exc)
