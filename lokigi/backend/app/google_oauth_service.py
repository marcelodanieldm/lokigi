"""google_oauth_service.py — Google OAuth2 login flow (openid email profile).

This is for *user login only*, NOT for Google Business Profile API access.
Uses httpx directly — no authlib dependency needed.

Flow
────
1. Frontend: GET /api/auth/google  →  redirect to Google consent screen
2. Google:   GET /api/auth/google/callback?code=...&state=...
3. Backend:  exchange code → get userinfo → find/create User → issue JWT
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from urllib.parse import urlencode

import httpx

from .config import settings

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


# ── CSRF state signing (itsdangerous-free, HMAC-SHA256) ──────────────────────

def _sign_state(value: str) -> str:
    sig = hmac.new(
        settings.oauth_state_secret.encode(), value.encode(), hashlib.sha256
    ).hexdigest()
    return f"{value}.{sig}"


def _verify_state_raw(signed: str) -> str | None:
    if "." not in signed:
        return None
    value, sig = signed.rsplit(".", 1)
    expected = hmac.new(
        settings.oauth_state_secret.encode(), value.encode(), hashlib.sha256
    ).hexdigest()
    if hmac.compare_digest(sig, expected):
        return value
    return None


# ── Public helpers ────────────────────────────────────────────────────────────

def build_login_url(next_url: str = "/dashboard", enterprise_slug: str = "") -> str:
    """Returns the Google OAuth2 authorization URL with a signed CSRF state."""
    nonce = secrets.token_urlsafe(16)
    # Encode next_url and enterprise_slug into state (pipe-separated)
    state_raw = f"{nonce}|{next_url}|{enterprise_slug}"
    state = _sign_state(state_raw)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_login_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
        "access_type": "online",
    }
    return f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"


def verify_state(state: str) -> tuple[str, str] | None:
    """Returns (next_url, enterprise_slug) or None if state is invalid/tampered."""
    raw = _verify_state_raw(state)
    if not raw:
        return None
    parts = raw.split("|", 2)
    if len(parts) < 3:
        return None
    return parts[1], parts[2]


def exchange_code(code: str) -> dict:
    """Exchange authorization code for Google userinfo.

    Returns a dict with keys: id, email, verified_email, name, picture.
    Raises httpx.HTTPStatusError on failure.
    """
    with httpx.Client(timeout=15) as client:
        token_resp = client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_login_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        userinfo_resp = client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_resp.raise_for_status()
        return userinfo_resp.json()
