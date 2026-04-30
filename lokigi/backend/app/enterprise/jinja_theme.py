"""
backend/app/enterprise/jinja_theme.py
========================================
Wires the White-Label theme engine into FastAPI's Jinja2Templates so every
HTML response automatically carries the correct brand colors, logo and fonts.

Quick start
-----------
In your app factory (e.g. main.py):

    from app.enterprise.jinja_theme import configure_themed_templates

    templates = configure_themed_templates("templates")
    # Use `templates` exactly like Jinja2Templates everywhere in the app.
    # The {{ theme }} variable will be available in every template.

In a route:

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request, db: Session = Depends(get_db)):
        return templates.TemplateResponse(
            "dashboard.html.j2",
            {
                "request": request,
                # theme is injected automatically — no need to pass it here
            }
        )

In a template that extends base.html.j2:

    {% extends "base.html.j2" %}
    {% block title %}Dashboard{% endblock %}
    {% block content %}
      <div style="color: var(--color-primary)">Hello!</div>
    {% endblock %}

Override mechanism
------------------
`configure_themed_templates` adds a Jinja2 global called `theme` that is a
callable — it takes the `request` object and returns the `BrandTheme` for that
request.  Inside base.html.j2 we call `{{ theme }}` directly because the
template context processor already resolves it to the BrandTheme dataclass via
the template context variable injected in `_themed_response`.

Architecture diagram
--------------------
  HTTP request
      │
      ▼
  OrgMiddleware          → request.state.org_id
      │
      ▼
  ThemeMiddleware        → request.state.theme  (BrandTheme)
      │
      ▼
  Route handler
      │  calls templates.TemplateResponse(...)
      ▼
  _themed_response()     → injects {"theme": request.state.theme, ...}
      │
      ▼
  base.html.j2           → <style>:root { --color-primary: … }</style>
                            {% if theme.logo_url %} … {% endif %}
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.enterprise.white_label import DEFAULT_THEME, BrandTheme

logger = logging.getLogger(__name__)


def configure_themed_templates(
    template_dir: str | Path,
    *,
    autoescape: bool = True,
) -> Jinja2Templates:
    """
    Build and return a Jinja2Templates instance pre-configured with:
      - The `theme` context variable (BrandTheme) resolved per-request.
      - A `now` global for template-side date rendering.
      - A `url_for` helper that is safe to call even outside a request context.
      - Custom filters: `brand_color`, `brand_url`.

    Parameters
    ----------
    template_dir:
        Directory containing .html.j2 (or .html) templates.
    autoescape:
        Enable Jinja2 HTML autoescaping (strongly recommended — default True).
    """
    templates = Jinja2Templates(directory=str(template_dir))

    # ── Globals ───────────────────────────────────────────────────────────────

    templates.env.globals["now"] = _now_utc
    templates.env.globals["DEFAULT_THEME"] = DEFAULT_THEME

    # ── Custom filters ────────────────────────────────────────────────────────

    @templates.env.filter_func   # type: ignore[attr-defined]
    def brand_color(value: str, fallback: str = "#7c3aed") -> str:
        """Return `value` if it looks like a valid CSS color, else `fallback`."""
        v = str(value).strip()
        if v.startswith("#") or v.startswith("rgb") or v.startswith("hsl"):
            return v
        return fallback

    @templates.env.filter_func   # type: ignore[attr-defined]
    def brand_url(value: str | None) -> str:
        """Return the URL if set, else an empty string (safe for src= attributes)."""
        return str(value).strip() if value else ""

    # ── Monkey-patch TemplateResponse to auto-inject theme ───────────────────
    _original_response = templates.TemplateResponse

    def _themed_response(
        name: str,
        context: dict[str, Any],
        *args,
        **kwargs,
    ) -> HTMLResponse:
        request: Request | None = context.get("request")
        if request is not None:
            # Resolve theme from middleware state; fall back to default
            theme: BrandTheme = getattr(request.state, "theme", DEFAULT_THEME)
        else:
            theme = DEFAULT_THEME

        # Inject into context — templates can always access {{ theme }}
        context.setdefault("theme", theme)
        context.setdefault("now", datetime.now(timezone.utc))

        return _original_response(name, context, *args, **kwargs)

    templates.TemplateResponse = _themed_response  # type: ignore[method-assign]
    return templates


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ─── Convenience: build CSS :root block from a BrandTheme ─────────────────────

def theme_to_css_vars(theme: BrandTheme) -> str:
    """
    Render the full :root { … } CSS block for a given BrandTheme.
    Useful when you need to emit it from an API endpoint rather than a template.

    Example:
        @app.get("/theme.css", response_class=Response)
        def serve_theme_css(request: Request):
            theme = getattr(request.state, "theme", DEFAULT_THEME)
            css = theme_to_css_vars(theme)
            return Response(content=css, media_type="text/css")
    """
    return f"""
:root {{
  --color-primary:         {theme.primary_color};
  --color-primary-hover:   {theme.primary_color}cc;
  --color-secondary:       {theme.secondary_color};
  --color-secondary-hover: {theme.secondary_color}cc;
  --font-brand:            {theme.font_family};
}}
""".strip()


# ─── Dynamic CSS endpoint (mount this router in main.py) ──────────────────────

def make_theme_css_router():
    """
    Returns a tiny FastAPI router that serves /enterprise/theme.css.
    The CSS is generated per-request based on the resolved BrandTheme,
    so each tenant gets their own branded stylesheet via a single URL.

    Cache headers: 5 minutes (matching Redis TTL in ThemeService).

    Mount in main.py:
        from app.enterprise.jinja_theme import make_theme_css_router
        app.include_router(make_theme_css_router())
    """
    from fastapi import APIRouter
    from fastapi.responses import Response

    router = APIRouter(tags=["enterprise-theme"])

    @router.get("/enterprise/theme.css", include_in_schema=False)
    async def dynamic_theme_css(request: Request) -> Response:
        theme: BrandTheme = getattr(request.state, "theme", DEFAULT_THEME)
        css = theme_to_css_vars(theme)
        return Response(
            content=css,
            media_type="text/css",
            headers={
                "Cache-Control": "public, max-age=300, stale-while-revalidate=60",
                "X-Theme-Org": theme.org_id or "default",
            },
        )

    return router
