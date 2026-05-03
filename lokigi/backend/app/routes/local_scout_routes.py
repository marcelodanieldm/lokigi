"""routes/local_scout_routes.py — Local Scout API: radar data + dashboard page."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.local_scout_service import SentimentDeltaService
from app.models import CompetitorEntity, User

router = APIRouter(prefix="/growth/local-scout", tags=["local-scout"])

templates = Jinja2Templates(directory="app/templates")


# ──────────────────────────────────────────────────────────────────────────────
# JSON API – radar data (consumed by Chart.js async fetch)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/radar", summary="Return Positioning Radar data for Chart.js")
def get_radar_data(user_id: UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = SentimentDeltaService(db)
    radar = service.compute_radar(user_id)

    labels = list(radar["client"].keys())
    client_scores = list(radar["client"].values())

    rival_datasets = [
        {
            "label": r["label"],
            "data": [r["scores"][lbl] for lbl in labels],
            "borderColor": f"rgba(251,191,36,{0.7 - i * 0.12})",
            "backgroundColor": f"rgba(251,191,36,{0.06 - i * 0.01})",
            "pointBackgroundColor": "rgba(251,191,36,0.8)",
            "borderDash": [4, 4],
        }
        for i, r in enumerate(radar["rivals"][:5])
    ]

    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Tu negocio",
                "data": client_scores,
                "borderColor": "rgba(52,211,153,1)",
                "backgroundColor": "rgba(52,211,153,0.15)",
                "pointBackgroundColor": "rgba(52,211,153,1)",
                "borderWidth": 2,
            },
            *rival_datasets,
        ],
        "axes": radar["client"],
        "has_data": radar["has_data"],
        "scraped_at": radar["scraped_at"].isoformat() if radar["scraped_at"] else None,
    }


# ──────────────────────────────────────────────────────────────────────────────
# HTML dashboard page
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/dashboard", response_class=HTMLResponse, summary="Local Scout radar dashboard")
def local_scout_dashboard(request: Request, user_id: UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    competitors = db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(CompetitorEntity)
        .where(
            CompetitorEntity.user_id == user_id,
            CompetitorEntity.status == "active",
        )
    ).scalars().all()

    return templates.TemplateResponse(
        "local_scout_radar.html",
        {
            "request": request,
            "user_id": str(user_id),
            "competitor_count": len(competitors),
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# Trigger on-demand scrape (returns task_id)
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/scrape/trigger", summary="Trigger an on-demand Local Scout scrape")
def trigger_scrape(user_id: UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    from tasks.local_scout import run_local_scout_for_user
    task = run_local_scout_for_user.delay(str(user_id))
    return {"ok": True, "task_id": task.id}
