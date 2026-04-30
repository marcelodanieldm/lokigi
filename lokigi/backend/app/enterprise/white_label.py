"""
backend/app/enterprise/white_label.py
=========================================
White-Label Theme Engine for Lokigi Enterprise.

How it works
------------
1.  `ThemeService.get_theme(domain, db)` — resolves the `Organization` row
    for the incoming HTTP domain and returns a `BrandTheme` dataclass.

2.  `ThemeMiddleware` — FastAPI middleware that attaches the resolved theme
    to `request.state.theme` so every Jinja2 template can access it without
    an extra DB query.

3.  `theme_context_processor` — Starlette / Jinja2 context function that
    injects theme variables as CSS custom properties into every HTML response.

Jinja2 template usage
---------------------
In your base template (e.g. base.html.j2) add inside <head>:

    <style>
      :root {
        --color-primary:   {{ theme.primary_color }};
        --color-secondary: {{ theme.secondary_color }};
        --font-brand:      {{ theme.font_family }};
      }
    </style>

    {% if theme.logo_url %}
    <img src="{{ theme.logo_url | e }}" alt="{{ theme.agency_name | e }}" class="h-10" />
    {% else %}
    <span class="font-black text-[--color-primary]">{{ theme.agency_name | e }}</span>
    {% endif %}

Replace hard-coded Tailwind color classes like `bg-violet-600` with
`bg-[--color-primary]` to make them dynamic.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

if TYPE_CHECKING:
    from app.enterprise.multi_tenancy import Organization

logger = logging.getLogger(__name__)


# ─── Theme dataclass ──────────────────────────────────────────────────────────

@dataclass
class BrandTheme:
    """Resolved theme for a single HTTP request / organization."""
    org_id: str | None = None
    agency_name: str = "Lokigi"
    agency_email: str = "hola@lokigi.com"
    primary_color: str = "#7c3aed"     # violet-600
    secondary_color: str = "#4f46e5"   # indigo-600
    logo_url: str | None = None
    font_family: str = "Arial, sans-serif"

    # Computed helpers
    @property
    def css_vars(self) -> str:
        """Ready-to-embed CSS :root block."""
        return (
            ":root {"
            f"  --color-primary: {self.primary_color};"
            f"  --color-secondary: {self.secondary_color};"
            f"  --font-brand: {self.font_family};"
            "}"
        )

    @property
    def cache_key(self) -> str:
        return hashlib.md5(
            f"{self.org_id}:{self.primary_color}:{self.secondary_color}".encode()
        ).hexdigest()


# Singleton default theme (used when no org is resolved)
DEFAULT_THEME = BrandTheme()


# ─── Theme service ────────────────────────────────────────────────────────────

class ThemeService:
    """
    Resolves the brand theme for a given HTTP host / domain.

    The organization table stores the canonical `domain` for each tenant
    (e.g. "analytics.pizza-norte.com").  On each request the middleware
    calls `get_theme(host)` which hits Redis first (L1 cache, 5 min TTL),
    then Postgres.
    """

    _CACHE_TTL = 300  # seconds

    def __init__(self, redis_client=None) -> None:
        # redis_client: optional aioredis / redis-py client instance
        self._redis = redis_client

    # ── Public API ────────────────────────────────────────────────────────────

    def get_theme(self, domain: str | None, db: Session) -> BrandTheme:
        """
        Resolve BrandTheme for `domain`.  Returns DEFAULT_THEME if not found.
        """
        if not domain:
            return DEFAULT_THEME

        # Normalise: strip port, lower-case
        host = domain.split(":")[0].lower()

        # L1: in-process dict cache (avoids redundant Redis round-trips within
        # the same worker process for the same domain within the same second)
        cached = _LOCAL_CACHE.get(host)
        if cached is not None:
            return cached

        # L2: Redis
        if self._redis is not None:
            try:
                raw = self._redis.get(f"theme:{host}")
                if raw:
                    theme = self._deserialize(raw)
                    _LOCAL_CACHE[host] = theme
                    return theme
            except Exception as exc:
                logger.warning("ThemeService Redis get failed: %s", exc)

        # L3: Postgres
        theme = self._load_from_db(host, db)
        self._write_cache(host, theme)
        return theme

    def invalidate(self, domain: str) -> None:
        """Call after updating an organization's theme settings."""
        host = domain.split(":")[0].lower()
        _LOCAL_CACHE.pop(host, None)
        if self._redis is not None:
            try:
                self._redis.delete(f"theme:{host}")
            except Exception as exc:
                logger.warning("ThemeService Redis delete failed: %s", exc)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _load_from_db(self, host: str, db: Session) -> BrandTheme:
        # Import here to avoid circular at module level
        from app.enterprise.multi_tenancy import Organization

        org: Organization | None = db.scalars(
            select(Organization).where(Organization.domain == host)
        ).first()

        if org is None:
            return DEFAULT_THEME

        return BrandTheme(
            org_id=str(org.id),
            agency_name=org.agency_name or org.name,
            agency_email=org.agency_email or "hola@lokigi.com",
            primary_color=org.primary_color,
            secondary_color=org.secondary_color,
            logo_url=org.logo_url,
        )

    def _write_cache(self, host: str, theme: BrandTheme) -> None:
        _LOCAL_CACHE[host] = theme
        if self._redis is not None:
            try:
                self._redis.setex(f"theme:{host}", self._CACHE_TTL, self._serialize(theme))
            except Exception as exc:
                logger.warning("ThemeService Redis set failed: %s", exc)

    @staticmethod
    def _serialize(theme: BrandTheme) -> str:
        import json
        return json.dumps({
            "org_id": theme.org_id,
            "agency_name": theme.agency_name,
            "agency_email": theme.agency_email,
            "primary_color": theme.primary_color,
            "secondary_color": theme.secondary_color,
            "logo_url": theme.logo_url,
            "font_family": theme.font_family,
        })

    @staticmethod
    def _deserialize(raw: bytes | str) -> BrandTheme:
        import json
        data = json.loads(raw)
        return BrandTheme(**data)


# Module-level L1 cache (per-process, lightweight)
_LOCAL_CACHE: dict[str, BrandTheme] = {}

# Module-level singleton service (swap redis_client in app startup)
theme_service = ThemeService()


# ─── Middleware ───────────────────────────────────────────────────────────────

class ThemeMiddleware(BaseHTTPMiddleware):
    """
    Resolves the brand theme from the request `Host` header and stores it
    at `request.state.theme`.

    Register AFTER OrgMiddleware so the org_id is already available.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        host = request.headers.get("host", "")
        try:
            from app.database import SessionLocal
            if SessionLocal is not None:
                with SessionLocal() as db:
                    request.state.theme = theme_service.get_theme(host, db)
            else:
                request.state.theme = DEFAULT_THEME
        except Exception as exc:
            logger.warning("ThemeMiddleware failed for host %s: %s", host, exc)
            request.state.theme = DEFAULT_THEME

        return await call_next(request)


# ─── Jinja2 context processor ─────────────────────────────────────────────────

def theme_context(request: Request) -> dict:
    """
    Pass this to Jinja2's global context so every template has {{ theme }}.

    Usage in FastAPI with Starlette templates:

        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="templates")
        templates.env.globals["theme"] = lambda req: getattr(req.state, "theme", DEFAULT_THEME)

    Or add it as a context override in each TemplateResponse:

        context = {"request": request, **theme_context(request)}
    """
    return {"theme": getattr(request.state, "theme", DEFAULT_THEME)}


# ─── FastAPI route for updating org theme (admin only) ───────────────────────

def make_theme_router():
    """
    Returns a FastAPI APIRouter with CRUD endpoints for org themes.
    Mount at /enterprise/theme.
    """
    from fastapi import APIRouter
    from pydantic import BaseModel

    from app.enterprise.multi_tenancy import Organization, get_current_org, require_org_id
    from app.database import get_db

    router = APIRouter(prefix="/enterprise/theme", tags=["enterprise-theme"])

    class ThemeUpdate(BaseModel):
        primary_color: str | None = None
        secondary_color: str | None = None
        logo_url: str | None = None
        agency_name: str | None = None
        agency_email: str | None = None

    @router.get("")
    def get_theme_settings(org: Organization = Depends(get_current_org)):
        return {
            "primary_color": org.primary_color,
            "secondary_color": org.secondary_color,
            "logo_url": org.logo_url,
            "agency_name": org.agency_name,
            "agency_email": org.agency_email,
        }

    @router.patch("")
    def update_theme(
        payload: ThemeUpdate,
        org: Organization = Depends(get_current_org),
        db: Session = Depends(get_db),
    ):
        for key, value in payload.model_dump(exclude_none=True).items():
            setattr(org, key, value)
        db.commit()
        db.refresh(org)

        # Invalidate cache for this org's domain
        if org.domain:
            theme_service.invalidate(org.domain)

        return {"ok": True, "updated": payload.model_dump(exclude_none=True)}

    return router
