"""routes/ceo_routes.py — CEO Command Center endpoints.

Authentication
──────────────
All routes require the  X-CEO-Key  header matching settings.ceo_api_key.
This is a simple shared-secret guard; replace with JWT / OAuth if needed.

Endpoints
─────────
GET  /api/v1/ceo/financials          → JSON KPI payload (Redis-cached 5 min)
POST /api/v1/ceo/financials/refresh  → force-invalidates cache and returns fresh data
GET  /ceo/dashboard                  → Jinja2 HTML dashboard (Executive Dark)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.ceo_financial_service import get_financial_kpis, invalidate_financial_cache
from app.config import settings
from app.database import get_db

router = APIRouter(tags=["ceo"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Auth guard
# ──────────────────────────────────────────────────────────────────────────────


def _require_ceo_key(x_ceo_key: str | None = Header(default=None, alias="X-CEO-Key")) -> None:
    if not x_ceo_key or x_ceo_key != settings.ceo_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-CEO-Key header",
        )


# ──────────────────────────────────────────────────────────────────────────────
# JSON API
# ──────────────────────────────────────────────────────────────────────────────


@router.get(
    "/api/v1/ceo/financials",
    summary="CEO financial KPIs (MRR, Churn, LTV) — Redis-cached 5 min",
    dependencies=[Depends(_require_ceo_key)],
)
def get_financials(db: Session = Depends(get_db)) -> dict[str, Any]:
    return get_financial_kpis(db)


@router.post(
    "/api/v1/ceo/financials/refresh",
    summary="Force-refresh CEO financial KPI cache",
    dependencies=[Depends(_require_ceo_key)],
)
def refresh_financials(db: Session = Depends(get_db)) -> dict[str, Any]:
    invalidate_financial_cache()
    return get_financial_kpis(db, force_refresh=True)


# ──────────────────────────────────────────────────────────────────────────────
# HTML dashboard (HTMX polling every 5 min)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/ceo/dashboard", response_class=HTMLResponse, summary="CEO Executive Dashboard")
def ceo_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    x_ceo_key: str | None = Header(default=None, alias="X-CEO-Key"),
):
    # Also accept the key as a query param for browser convenience (dev mode only)
    qkey = request.query_params.get("key")
    key_to_check = x_ceo_key or qkey
    if not key_to_check or key_to_check != settings.ceo_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = get_financial_kpis(db)
    return templates.TemplateResponse(
        "ceo_dashboard.html",
        {"request": request, "kpis": data, "ceo_key": key_to_check},
    )
