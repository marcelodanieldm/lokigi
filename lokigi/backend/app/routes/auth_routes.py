"""routes/auth_routes.py — Authentication & session management.

HTML screens
────────────
  GET  /login                        Pantalla A: Login universal (Starter/Growth)
  GET  /login/enterprise/{slug}      Pantalla B: Login white-label (Enterprise)
  GET  /login/ceo                    CEO login (IP whitelist + TOTP)
  GET  /auth/2fa                     Pantalla C: TOTP / device-verify screen
  GET  /auth/password/reset          Password reset form

Auth API
────────
  POST /api/auth/token               Email + password → JWT cookie (HTMX-friendly)
    GET  /auth/login                   Redirect to Google consent screen
    GET  /auth/callback                OAuth2 callback → JWT cookie
  POST /api/auth/2fa/verify          Verify TOTP code
  POST /api/auth/device-verify       Verify email OTP (suspicious IP)
  POST /api/auth/logout              Blacklist token + clear cookie
  POST /api/auth/password/forgot     Send reset email
  POST /api/auth/password/reset      Apply new password

Enterprise config API
────────────────────
  POST /api/v1/enterprise/config     Create/update EnterpriseConfig for an org
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import jwt
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth_service import (
    blacklist_token,
    consume_reset_token,
    decode_access_token,
    encode_pending_state,
    decode_pending_state,
    fingerprint_ip,
    generate_device_code,
    generate_reset_token,
    generate_totp_secret,
    get_totp_provisioning_uri,
    hash_password,
    is_account_locked,
    is_suspicious_ip,
    record_failed_attempt,
    record_session,
    reset_failed_attempts,
    verify_device_code,
    verify_password,
    verify_totp,
    create_access_token,
)
from app.config import settings
from app.database import get_db
from app.models import (
    EnterpriseConfig,
    OrgMember,
    Organization,
    SubscriptionProfile,
    User,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

# Cookie name for the JWT access token
_COOKIE = "access_token"
# Cookie name for the pending MFA/device-verify state
_PENDING_COOKIE = "pending_auth"

oauth = OAuth()
oauth.register(
    name="google_login",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "select_account",
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _set_jwt_cookie(response: Any, token: str) -> None:
    response.set_cookie(
        key=_COOKIE,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=settings.jwt_access_token_expire_hours * 3600,
        path="/",
    )


def _clear_auth_cookies(response: Any) -> None:
    response.delete_cookie(_COOKIE, path="/")
    response.delete_cookie(_PENDING_COOKIE, path="/")


def _get_request_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_user_plan(db: Session, user: User) -> str:
    profile = db.execute(
        select(SubscriptionProfile).where(SubscriptionProfile.user_id == user.id)
    ).scalar_one_or_none()
    return profile.subscription_plan if profile else "starter"


_ACTIVE_STATUSES = {"active", "trialing", "past_due"}
_PLAN_DASHBOARDS = {
    "starter": "/starter/inbox",
    "growth": "/growth/dashboard",
    "enterprise": "/dashboard/enterprise",
}


def _resolve_post_login_url(db: Session, user: User) -> str:
    """Return the correct post-login destination based on subscription state."""
    profile = db.execute(
        select(SubscriptionProfile).where(SubscriptionProfile.user_id == user.id)
    ).scalar_one_or_none()
    if profile is None or profile.subscription_status not in _ACTIVE_STATUSES:
        return "/onboarding/select-plan"
    plan = profile.subscription_plan or "starter"
    return _PLAN_DASHBOARDS.get(plan, "/onboarding/select-plan")


def _get_primary_org(db: Session, user_id: UUID) -> OrgMember | None:
    """Returns the first active OrgMember row for this user (owner first)."""
    return db.execute(
        select(OrgMember)
        .where(OrgMember.user_id == user_id, OrgMember.status == "active")
        .order_by(OrgMember.role)  # owner < admin < member < viewer alphabetically
        .limit(1)
    ).scalar_one_or_none()


def _send_email_code(email: str, code: str) -> None:
    """Fire-and-forget: send device verification code via SendGrid."""
    if not settings.sendgrid_api_key:
        logger.warning("SendGrid not configured — skipping device code email")
        return
    try:
        import httpx as _httpx
        _httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
            json={
                "from": {"email": settings.sendgrid_from_email},
                "to": [{"email": email}],
                "subject": "Código de verificación — Lokigi",
                "content": [{
                    "type": "text/html",
                    "value": (
                        f"<p>Tu código de verificación es:</p>"
                        f"<h1 style='letter-spacing:8px;font-family:monospace'>{code}</h1>"
                        f"<p>Válido por <strong>10 minutos</strong>. "
                        f"Si no intentaste iniciar sesión, ignora este correo.</p>"
                    ),
                }],
            },
            timeout=10,
        )
    except Exception as exc:
        logger.error("SendGrid error sending device code: %s", exc)


def _send_reset_email(email: str, token: str) -> None:
    if not settings.sendgrid_api_key:
        logger.warning("SendGrid not configured — skipping reset email")
        return
    reset_url = f"https://{settings.app_domain}/auth/password/reset?token={token}"
    try:
        import httpx as _httpx
        _httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
            json={
                "from": {"email": settings.sendgrid_from_email},
                "to": [{"email": email}],
                "subject": "Recuperación de contraseña — Lokigi",
                "content": [{
                    "type": "text/html",
                    "value": (
                        f"<p>Haz clic en el siguiente enlace para restablecer tu contraseña:</p>"
                        f"<p><a href='{reset_url}' style='background:#6366f1;color:#fff;"
                        f"padding:12px 24px;border-radius:6px;text-decoration:none'>"
                        f"Restablecer contraseña</a></p>"
                        f"<p style='color:#6b7280;font-size:12px'>Enlace válido por 1 hora.</p>"
                    ),
                }],
            },
            timeout=10,
        )
    except Exception as exc:
        logger.error("SendGrid error sending reset email: %s", exc)


def _ip_is_allowed_for_ceo(ip: str) -> bool:
    allowed = [x.strip() for x in settings.ceo_allowed_ips.split(",") if x.strip()]
    if not allowed:
        return True  # Dev mode — no restriction
    return ip in allowed


# ─────────────────────────────────────────────────────────────────────────────
# HTML screen endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request, next: str = "/dashboard", error: str | None = None):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": next,
        "error": error,
        "google_enabled": bool(settings.google_client_id),
    })


@router.get("/login/enterprise/{slug}", response_class=HTMLResponse, include_in_schema=False)
def login_enterprise_page(slug: str, request: Request, next: str = "/dashboard"):
    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        org = db.execute(
            select(Organization).where(Organization.slug == slug, Organization.status == "active")
        ).scalar_one_or_none()
        if not org:
            return RedirectResponse(url="/login?error=org_not_found", status_code=302)
        cfg = db.execute(
            select(EnterpriseConfig).where(EnterpriseConfig.org_id == org.id)
        ).scalar_one_or_none()
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

    return templates.TemplateResponse("login_enterprise.html", {
        "request": request,
        "org": org,
        "cfg": cfg,
        "next": next,
        "google_enabled": bool(settings.google_client_id),
    })


@router.get("/login/ceo", response_class=HTMLResponse, include_in_schema=False)
def login_ceo_page(request: Request):
    ip = _get_request_ip(request)
    if not _ip_is_allowed_for_ceo(ip):
        raise HTTPException(status_code=403, detail="Acceso denegado desde esta dirección IP.")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": "/ceo/dashboard",
        "ceo_mode": True,
        "google_enabled": False,  # CEO must use email/TOTP
    })


@router.get("/auth/2fa", response_class=HTMLResponse, include_in_schema=False)
def twofa_page(request: Request):
    pending_raw = request.cookies.get(_PENDING_COOKIE, "")
    state = decode_pending_state(pending_raw) if pending_raw else None
    if not state:
        return RedirectResponse(url="/login?error=session_expired", status_code=302)
    return templates.TemplateResponse("login_2fa.html", {
        "request": request,
        "mfa_type": state.get("mfa_type", "totp"),
    })


@router.get("/auth/password/reset", response_class=HTMLResponse, include_in_schema=False)
def password_reset_page(request: Request, token: str = ""):
    return templates.TemplateResponse("login_password_reset.html", {
        "request": request,
        "token": token,
    })


@router.get("/auth/link-google", response_class=HTMLResponse, include_in_schema=False)
def link_google_page(request: Request):
    pending = request.session.get("google_link")
    if not pending:
        return RedirectResponse(url="/login?error=session_expired", status_code=302)
    return templates.TemplateResponse("login_google_link.html", {
        "request": request,
        "email": pending.get("email", ""),
    })


@router.post("/auth/link-google")
def confirm_link_google(
    request: Request,
    action: str = Form(default="confirm"),
    db: Session = Depends(get_db),
):
    pending = request.session.pop("google_link", None)
    if not pending:
        return RedirectResponse(url="/login?error=session_expired", status_code=302)

    if action.strip().lower() == "cancel":
        return RedirectResponse(url="/login", status_code=302)

    email = (pending.get("email") or "").lower().strip()
    google_id = pending.get("google_id") or ""
    next_url = pending.get("next") or "/dashboard"
    if not email or not google_id:
        return RedirectResponse(url="/login?error=google_auth_failed", status_code=302)

    user: User | None = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        return RedirectResponse(url=f"/onboarding?email={email}&provider=google", status_code=302)

    # Safety: avoid linking a Google identity already bound to another account.
    existing_google = db.execute(select(User).where(User.google_id == google_id)).scalar_one_or_none()
    if existing_google and existing_google.id != user.id:
        return RedirectResponse(url="/login?error=google_already_linked", status_code=302)

    user.google_id = google_id
    user.auth_provider = "google"
    db.commit()

    plan = _get_user_plan(db, user)
    member = _get_primary_org(db, user.id)
    org_id = member.org_id if member else None
    role = member.role if member else "owner"

    ip = _get_request_ip(request)
    ua = request.headers.get("user-agent", "")
    record_session(db, user.id, fingerprint_ip(ip, ua), ua)
    token = create_access_token(user.id, org_id, role, plan)

    resp = RedirectResponse(url=next_url, status_code=302)
    _set_jwt_cookie(resp, token)
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/token — Email + Password login (HTMX-friendly)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/auth/token", response_class=HTMLResponse)
async def login_token(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(default="/dashboard"),
    db: Session = Depends(get_db),
):
    def _err(msg: str) -> HTMLResponse:
        return HTMLResponse(
            f'<div id="error-msg" class="auth-error">{msg}</div>',
            status_code=200,
        )

    # Find user
    user: User | None = db.execute(
        select(User).where(User.email == email.lower().strip())
    ).scalar_one_or_none()

    if not user or not user.password_hash:
        return _err("Credenciales inválidas. Verifica tu email y contraseña.")

    # Lockout check
    if is_account_locked(user):
        return _err(
            f"Cuenta bloqueada temporalmente por múltiples intentos fallidos. "
            f"Intenta de nuevo en {settings.login_lockout_minutes} minutos."
        )

    # Password check
    if not verify_password(password, user.password_hash):
        record_failed_attempt(db, user)
        return _err("Credenciales inválidas. Verifica tu email y contraseña.")

    reset_failed_attempts(db, user)

    # Build auth context
    plan = _get_user_plan(db, user)
    member = _get_primary_org(db, user.id)
    org_id = member.org_id if member else None
    role = member.role if member else "owner"

    # Device fingerprint / suspicious IP check (skip for CEO TOTP flow)
    ip = _get_request_ip(request)
    ua = request.headers.get("user-agent", "")
    ip_hash = fingerprint_ip(ip, ua)
    suspicious = is_suspicious_ip(db, user.id, ip_hash)

    # Check if MFA is required
    need_mfa = user.mfa_enabled and user.mfa_secret
    need_device = suspicious and not need_mfa  # Only device check if MFA not already required

    if need_mfa:
        pending = encode_pending_state(user.id, org_id, role, plan, "totp")
        resp = HTMLResponse("")
        resp.set_cookie(_PENDING_COOKIE, pending, httponly=True, max_age=600, path="/")
        resp.headers["HX-Redirect"] = "/auth/2fa"
        return resp

    if need_device:
        code = generate_device_code(db, user.id)
        _send_email_code(user.email, code)
        pending = encode_pending_state(user.id, org_id, role, plan, "device")
        resp = HTMLResponse("")
        resp.set_cookie(_PENDING_COOKIE, pending, httponly=True, max_age=600, path="/")
        resp.headers["HX-Redirect"] = "/auth/2fa"
        return resp

    # Issue JWT
    record_session(db, user.id, ip_hash, ua)
    token = create_access_token(user.id, org_id, role, plan)
    resp = HTMLResponse("")
    _set_jwt_cookie(resp, token)
    dest = next if next and next not in ("/dashboard", "") else _resolve_post_login_url(db, user)
    resp.headers["HX-Redirect"] = dest
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# Google OAuth2
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/auth/login")
async def google_auth_redirect(
    request: Request,
    next: str = Query(default="/dashboard"),
    enterprise_slug: str = Query(default=""),
):
    if not settings.google_client_id:
        raise HTTPException(400, "Google login not configured")
    request.session["oauth_next_url"] = next
    request.session["oauth_enterprise_slug"] = enterprise_slug
    redirect_uri = settings.google_login_redirect_uri or str(request.url_for("google_auth_callback"))

    client = oauth.create_client("google_login")
    if client is None:
        raise HTTPException(500, "Google OAuth client initialization failed")

    if request.headers.get("HX-Request") == "true":
        auth_url, _ = client.create_authorization_url(redirect_uri)
        response = HTMLResponse("")
        response.headers["HX-Redirect"] = auth_url
        return response

    return await client.authorize_redirect(request, redirect_uri)


@router.get("/api/auth/google")
async def google_auth_redirect_legacy(
    request: Request,
    next: str = Query(default="/dashboard"),
    enterprise_slug: str = Query(default=""),
):
    return await google_auth_redirect(request=request, next=next, enterprise_slug=enterprise_slug)


@router.get("/auth/callback", name="google_auth_callback")
async def google_auth_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    client = oauth.create_client("google_login")
    if client is None:
        return RedirectResponse(url="/login?error=google_auth_failed", status_code=302)

    try:
        token_payload = await client.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(url="/login?error=google_auth_failed", status_code=302)

    userinfo = token_payload.get("userinfo") or {}
    if not userinfo and token_payload.get("access_token"):
        userinfo_resp = await client.get("https://openidconnect.googleapis.com/v1/userinfo", token=token_payload)
        userinfo = userinfo_resp.json() if userinfo_resp else {}

    email = (userinfo.get("email") or "").lower().strip()
    google_id = (userinfo.get("sub") or userinfo.get("id") or "").strip()
    verified_email = bool(userinfo.get("email_verified", userinfo.get("verified_email", False)))
    if not email or not google_id or not verified_email:
        return RedirectResponse(url="/login?error=no_email", status_code=302)

    next_url = request.session.pop("oauth_next_url", "/dashboard")
    request.session.pop("oauth_enterprise_slug", "")

    # Soberania Lokigi: reconcile account by email in our DB.
    user: User | None = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if not user:
        return RedirectResponse(
            url=f"/onboarding?email={email}&provider=google",
            status_code=302,
        )

    existing_google_owner = db.execute(
        select(User).where(User.google_id == google_id)
    ).scalar_one_or_none()
    if existing_google_owner and existing_google_owner.id != user.id:
        return RedirectResponse(url="/login?error=google_already_linked", status_code=302)

    # First Google login for an existing account: ask explicit linking confirmation.
    if not user.google_id:
        request.session["google_link"] = {
            "email": email,
            "google_id": google_id,
            "next": next_url,
        }
        return RedirectResponse(url="/auth/link-google", status_code=302)

    if user.google_id != google_id:
        return RedirectResponse(url="/login?error=google_mismatch", status_code=302)

    user.auth_provider = "google"
    db.commit()

    plan = _get_user_plan(db, user)
    member = _get_primary_org(db, user.id)
    org_id = member.org_id if member else None
    role = member.role if member else "owner"

    # Device check
    ip = _get_request_ip(request)
    ua = request.headers.get("user-agent", "")
    ip_hash = fingerprint_ip(ip, ua)
    suspicious = is_suspicious_ip(db, user.id, ip_hash)

    if suspicious and user.mfa_enabled and user.mfa_secret:
        pending = encode_pending_state(user.id, org_id, role, plan, "totp")
        resp = RedirectResponse(url="/auth/2fa", status_code=302)
        resp.set_cookie(_PENDING_COOKIE, pending, httponly=True, max_age=600, path="/")
        return resp

    if suspicious:
        code_otp = generate_device_code(db, user.id)
        _send_email_code(user.email, code_otp)
        pending = encode_pending_state(user.id, org_id, role, plan, "device")
        resp = RedirectResponse(url="/auth/2fa", status_code=302)
        resp.set_cookie(_PENDING_COOKIE, pending, httponly=True, max_age=600, path="/")
        return resp

    record_session(db, user.id, ip_hash, ua)
    token = create_access_token(user.id, org_id, role, plan)
    smart_url = next_url if next_url and next_url not in ("/dashboard", "") else _resolve_post_login_url(db, user)
    resp = RedirectResponse(url=smart_url, status_code=302)
    _set_jwt_cookie(resp, token)
    return resp


@router.get("/api/auth/google/callback")
async def google_auth_callback_legacy(request: Request, db: Session = Depends(get_db)):
    return await google_auth_callback(request=request, db=db)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/2fa/verify — TOTP verification (HTMX-friendly)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/auth/2fa/verify", response_class=HTMLResponse)
async def verify_2fa(
    request: Request,
    code: str = Form(...),
    db: Session = Depends(get_db),
):
    def _err(msg: str) -> HTMLResponse:
        return HTMLResponse(f'<div id="mfa-error" class="auth-error">{msg}</div>', status_code=200)

    pending_raw = request.cookies.get(_PENDING_COOKIE, "")
    state = decode_pending_state(pending_raw) if pending_raw else None
    if not state:
        return _err("Sesión expirada. Vuelve a iniciar sesión.")

    user_id = UUID(state["user_id"])
    org_id = UUID(state["org_id"]) if state.get("org_id") else None
    role = state.get("role", "owner")
    plan = state.get("plan", "starter")
    mfa_type = state.get("mfa_type", "totp")

    user: User | None = db.get(User, user_id)
    if not user:
        return _err("Usuario no encontrado.")

    if mfa_type == "totp":
        if not user.mfa_secret or not verify_totp(user.mfa_secret, code.strip()):
            return _err("Código incorrecto. Verifica tu aplicación autenticadora.")
    else:
        # Device OTP
        if not verify_device_code(db, user_id, code.strip()):
            return _err("Código inválido o expirado. Solicita uno nuevo.")

    # All checks passed — issue JWT
    ip = _get_request_ip(request)
    ua = request.headers.get("user-agent", "")
    record_session(db, user_id, fingerprint_ip(ip, ua), ua)
    token = create_access_token(user_id, org_id, role, plan)

    user_obj = db.get(User, user_id)
    resp = HTMLResponse("")
    _set_jwt_cookie(resp, token)
    resp.delete_cookie(_PENDING_COOKIE, path="/")
    resp.headers["HX-Redirect"] = _resolve_post_login_url(db, user_obj) if user_obj else "/onboarding/select-plan"
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/device-verify — Email OTP (alias of 2fa/verify for device flow)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/auth/device-verify", response_class=HTMLResponse)
async def verify_device(
    request: Request,
    code: str = Form(...),
    db: Session = Depends(get_db),
):
    # Reuse the same logic as 2fa/verify
    return await verify_2fa(request=request, code=code, db=db)


@router.post("/api/auth/device-verify/resend", response_class=HTMLResponse)
async def resend_device_code(request: Request, db: Session = Depends(get_db)):
    pending_raw = request.cookies.get(_PENDING_COOKIE, "")
    state = decode_pending_state(pending_raw) if pending_raw else None
    if not state or state.get("mfa_type") != "device":
        return HTMLResponse('<div id="mfa-error" class="auth-error">Sesion expirada. Inicia sesion nuevamente.</div>', status_code=200)

    user_id = UUID(state["user_id"])
    user: User | None = db.get(User, user_id)
    if not user:
        return HTMLResponse('<div id="mfa-error" class="auth-error">Usuario no encontrado.</div>', status_code=200)

    code = generate_device_code(db, user.id)
    _send_email_code(user.email, code)
    return HTMLResponse('<div id="mfa-error" class="auth-success">Te enviamos un nuevo codigo al correo.</div>', status_code=200)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/logout
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/auth/logout")
def logout(request: Request):
    token = request.cookies.get(_COOKIE, "")
    if token:
        try:
            data = decode_access_token(token)
            exp = data.get("exp", 0)
            ttl = max(exp - int(datetime.now(timezone.utc).timestamp()), 1)
            blacklist_token(token, ttl)
        except jwt.InvalidTokenError:
            pass  # Already expired — no need to blacklist

    resp = RedirectResponse(url="/login?msg=logout_seguro", status_code=302)
    _clear_auth_cookies(resp)
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# Password recovery
# ─────────────────────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/api/auth/password/forgot", response_class=HTMLResponse)
async def forgot_password(
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.execute(
        select(User).where(User.email == email.lower().strip())
    ).scalar_one_or_none()

    # Always return success to prevent email enumeration
    if user and user.password_hash:
        token = generate_reset_token(db, user.id)
        _send_reset_email(user.email, token)

    return HTMLResponse(
        '<div id="forgot-msg" class="auth-success">'
        "Si el correo existe, recibirás un enlace en los próximos minutos."
        "</div>"
    )


class ResetPasswordPayload(BaseModel):
    token: str
    password: str


@router.post("/api/auth/password/reset", response_class=HTMLResponse)
async def reset_password(
    token: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    def _err(msg: str) -> HTMLResponse:
        return HTMLResponse(f'<div id="reset-error" class="auth-error">{msg}</div>')

    if len(password) < 8:
        return _err("La contraseña debe tener al menos 8 caracteres.")

    user_id = consume_reset_token(db, token)
    if not user_id:
        return _err("El enlace de recuperación es inválido o ha expirado.")

    user: User | None = db.get(User, user_id)
    if not user:
        return _err("Usuario no encontrado.")

    user.password_hash = hash_password(password)
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    resp = HTMLResponse("")
    resp.headers["HX-Redirect"] = "/login?msg=password_reset_ok"
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# Enterprise config CRUD
# ─────────────────────────────────────────────────────────────────────────────

class EnterpriseConfigPayload(BaseModel):
    org_id: UUID
    logo_url: str | None = None
    brand_primary_color: str = "#6366f1"
    brand_bg_color: str = "#f8fafc"
    welcome_message: str | None = None
    login_domain: str | None = None
    mfa_required: bool = True
    min_password_length: int = 12


@router.post("/api/v1/enterprise/config")
def upsert_enterprise_config(
    payload: EnterpriseConfigPayload,
    db: Session = Depends(get_db),
):
    cfg = db.execute(
        select(EnterpriseConfig).where(EnterpriseConfig.org_id == payload.org_id)
    ).scalar_one_or_none()

    if not cfg:
        cfg = EnterpriseConfig(org_id=payload.org_id)
        db.add(cfg)

    cfg.logo_url = payload.logo_url
    cfg.brand_primary_color = payload.brand_primary_color
    cfg.brand_bg_color = payload.brand_bg_color
    cfg.welcome_message = payload.welcome_message
    cfg.login_domain = payload.login_domain
    cfg.mfa_required = payload.mfa_required
    cfg.min_password_length = payload.min_password_length
    db.commit()
    db.refresh(cfg)

    return {"id": str(cfg.id), "org_id": str(cfg.org_id), "status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# TOTP setup (for Enterprise/CEO users)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/v1/auth/totp/setup")
def setup_totp(
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    """Generate a new TOTP secret and return the QR provisioning URI.
    The frontend should display this as a QR code for the user to scan.
    Calling /api/v1/auth/totp/confirm activates it."""
    user: User | None = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    secret = generate_totp_secret()
    user.mfa_secret = secret
    # mfa_enabled stays False until confirmed
    db.commit()

    return {
        "secret": secret,
        "provisioning_uri": get_totp_provisioning_uri(secret, user.email),
    }


class TOTPConfirmPayload(BaseModel):
    user_id: UUID
    code: str


@router.post("/api/v1/auth/totp/confirm")
def confirm_totp(payload: TOTPConfirmPayload, db: Session = Depends(get_db)):
    user: User | None = db.get(User, payload.user_id)
    if not user or not user.mfa_secret:
        raise HTTPException(404, "TOTP no configurado")

    if not verify_totp(user.mfa_secret, payload.code):
        raise HTTPException(422, detail={"code": "INVALID_TOTP", "message": "Código incorrecto"})

    user.mfa_enabled = True
    db.commit()
    return {"status": "totp_enabled"}
