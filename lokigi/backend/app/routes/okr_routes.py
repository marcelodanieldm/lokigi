"""routes/okr_routes.py — OKR Monitor API + HTML dashboard.

All endpoints require X-CEO-Key header (same as CEO Command Center / CRM).

Endpoints
─────────
GET  /api/v1/okr                    → full OKR payload (JSON)
GET  /api/v1/okr/quarters           → list of available quarter/year pairs
POST /api/v1/okr/seed               → (re-)seed sample OKRs (dev utility)
PATCH /api/v1/okr/kr/{kr_id}/value  → manually set current_value_override for a KR
GET  /okr/dashboard                 → Jinja2 HTML OKR dashboard
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import OKRKeyResult, OKRObjective
from app.okr_service import build_okr_dashboard, ensure_seed_okrs

router = APIRouter(tags=["okr"])
templates = Jinja2Templates(directory="app/templates")


# ──────────────────────────────────────────────────────────────────────────────
# Auth guard (same as CEO Command Center)
# ──────────────────────────────────────────────────────────────────────────────


def _require_ceo_key(x_ceo_key: str | None = Header(default=None, alias="X-CEO-Key")) -> None:
    if not x_ceo_key or x_ceo_key != settings.ceo_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-CEO-Key header")


# ──────────────────────────────────────────────────────────────────────────────
# JSON API
# ──────────────────────────────────────────────────────────────────────────────


@router.get(
    "/api/v1/okr",
    summary="Full OKR dashboard payload",
    dependencies=[Depends(_require_ceo_key)],
)
def get_okr_dashboard(
    db: Session = Depends(get_db),
    quarter: int | None = Query(default=None, ge=1, le=4),
    year: int | None = Query(default=None, ge=2020, le=2030),
) -> dict[str, Any]:
    ensure_seed_okrs(db)
    return build_okr_dashboard(db, quarter=quarter, year=year)


@router.get(
    "/api/v1/okr/quarters",
    summary="List available quarter/year pairs",
    dependencies=[Depends(_require_ceo_key)],
)
def list_quarters(db: Session = Depends(get_db)) -> list[dict[str, int]]:
    rows = db.execute(
        select(distinct(OKRObjective.quarter), OKRObjective.year)
        .order_by(OKRObjective.year.desc(), OKRObjective.quarter.desc())
    ).all()
    return [{"quarter": r[0], "year": r[1]} for r in rows]


@router.post(
    "/api/v1/okr/seed",
    summary="Seed sample Q2-2026 OKRs (idempotent)",
    dependencies=[Depends(_require_ceo_key)],
)
def seed_okrs(db: Session = Depends(get_db)) -> dict[str, Any]:
    before = db.scalar(select(func.count(OKRObjective.id))) or 0
    ensure_seed_okrs(db)
    after = db.scalar(select(func.count(OKRObjective.id))) or 0
    return {"inserted": after - before, "total_objectives": after}


class KRValuePayload(BaseModel):
    value: float


@router.patch(
    "/api/v1/okr/kr/{kr_id}/value",
    summary="Manually set current value for a KR (when metric_source is 'manual')",
    dependencies=[Depends(_require_ceo_key)],
)
def set_kr_value(kr_id: uuid.UUID, payload: KRValuePayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    kr = db.get(OKRKeyResult, kr_id)
    if not kr:
        raise HTTPException(status_code=404, detail="KeyResult not found")
    kr.current_value_override = payload.value
    kr.updated_at = datetime.now(tz=timezone.utc)
    db.commit()
    return {"ok": True, "kr_id": str(kr_id), "current_value_override": float(kr.current_value_override)}


# ──────────────────────────────────────────────────────────────────────────────
# HTML Dashboard
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/okr/dashboard", response_class=HTMLResponse, summary="OKR Dashboard")
def okr_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    x_ceo_key: str | None = Header(default=None, alias="X-CEO-Key"),
    quarter: int | None = Query(default=None, ge=1, le=4),
    year: int | None = Query(default=None, ge=2020, le=2030),
):
    qkey = request.query_params.get("key")
    key_to_check = x_ceo_key or qkey
    if not key_to_check or key_to_check != settings.ceo_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    ensure_seed_okrs(db)
    data = build_okr_dashboard(db, quarter=quarter, year=year)

    # Build available quarters for the quarter-switcher nav
    quarters = db.execute(
        select(distinct(OKRObjective.quarter), OKRObjective.year)
        .order_by(OKRObjective.year.desc(), OKRObjective.quarter.desc())
    ).all()
    available_quarters = [{"quarter": r[0], "year": r[1]} for r in quarters]

    return templates.TemplateResponse(
        "okr_dashboard.html",
        {
            "request": request,
            "data": data,
            "ceo_key": key_to_check,
            "available_quarters": available_quarters,
        },
    )
