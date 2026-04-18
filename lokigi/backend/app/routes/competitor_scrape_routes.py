from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.competitor_scrape_ingest_service import CompetitorScrapeIngestService
from app.config import settings
from app.database import get_db
from app.models import CompetitorSnapshot, ScrapeRun, User

router = APIRouter(tags=["growth-competitor-scrape"])


class StartRunRequest(BaseModel):
    user_id: UUID
    total_targets: int = Field(default=5, ge=1, le=50)


class IngestSnapshotRequest(BaseModel):
    user_id: UUID
    run_id: UUID
    competitor_url: str = Field(min_length=10, max_length=1200)
    name: str | None = Field(default=None, max_length=120)
    zone_label: str | None = Field(default=None, max_length=120)
    rating_avg: float | None = Field(default=None, ge=0, le=5)
    review_count_total: int | None = Field(default=None, ge=0)
    price_level_raw: str | None = Field(default=None, max_length=8)
    category: str | None = Field(default=None, max_length=80)
    address_short: str | None = Field(default=None, max_length=255)
    posts_30d: int | None = Field(default=None, ge=0)
    services: list[str] = Field(default_factory=list)
    source_status: str = Field(default="ok", description="ok|partial|error|blocked")


class FinishRunRequest(BaseModel):
    user_id: UUID
    run_id: UUID
    forced_status: str | None = Field(default=None, description="ok|partial|error|blocked")


class SnapshotResponse(BaseModel):
    id: UUID
    run_id: UUID
    competitor_id: UUID
    observed_on: datetime | None
    rating_x100: int | None
    total_reviews: int | None
    price_bucket: str
    posts_30d: int | None
    source_status: str


def _validate_internal_secret(x_webhook_secret: str) -> None:
    if settings.webhook_shared_secret and x_webhook_secret != settings.webhook_shared_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")


@router.post("/internal/growth/competitor-scrape/run/start", summary="Start a lightweight scrape run")
def start_competitor_scrape_run(
    request: StartRunRequest,
    x_webhook_secret: str = Header(default="", alias="X-Webhook-Secret"),
    db: Session = Depends(get_db),
):
    _validate_internal_secret(x_webhook_secret)

    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = CompetitorScrapeIngestService(db)
    run = service.start_run(user_id=request.user_id, total_targets=request.total_targets)
    return {
        "ok": True,
        "run_id": run.id,
        "run_date": run.run_date,
        "total_targets": run.total_targets,
        "status": run.status,
    }


@router.post("/internal/growth/competitor-scrape/ingest", summary="Ingest one scraped competitor snapshot")
def ingest_competitor_scrape_snapshot(
    request: IngestSnapshotRequest,
    x_webhook_secret: str = Header(default="", alias="X-Webhook-Secret"),
    db: Session = Depends(get_db),
):
    _validate_internal_secret(x_webhook_secret)

    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = CompetitorScrapeIngestService(db)
    try:
        snapshot = service.ingest_competitor_snapshot(
            run_id=request.run_id,
            user_id=request.user_id,
            competitor_url=request.competitor_url,
            name=request.name,
            zone_label=request.zone_label,
            rating_avg=request.rating_avg,
            review_count_total=request.review_count_total,
            price_level_raw=request.price_level_raw,
            category=request.category,
            address_short=request.address_short,
            posts_30d=request.posts_30d,
            services=request.services,
            source_status=request.source_status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "ok": True,
        "snapshot_id": snapshot.id,
        "run_id": snapshot.scrape_run_id,
        "competitor_id": snapshot.competitor_id,
        "status": snapshot.source_status,
    }


@router.post("/internal/growth/competitor-scrape/run/finish", summary="Finish scrape run and lock counters")
def finish_competitor_scrape_run(
    request: FinishRunRequest,
    x_webhook_secret: str = Header(default="", alias="X-Webhook-Secret"),
    db: Session = Depends(get_db),
):
    _validate_internal_secret(x_webhook_secret)

    service = CompetitorScrapeIngestService(db)
    try:
        run = service.finish_run(
            run_id=request.run_id,
            user_id=request.user_id,
            forced_status=request.forced_status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "ok": True,
        "run_id": run.id,
        "status": run.status,
        "total_targets": run.total_targets,
        "total_processed": run.total_processed,
        "total_success": run.total_success,
        "total_failed": run.total_failed,
        "finished_at": run.finished_at,
    }


@router.get("/api/growth/competitor-scrape/runs", summary="List recent lightweight scrape runs")
def list_scrape_runs(
    user_id: UUID,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    rows = db.scalars(
        select(ScrapeRun)
        .where(ScrapeRun.user_id == user_id)
        .order_by(ScrapeRun.started_at.desc())
        .limit(limit)
    ).all()

    return [
        {
            "run_id": row.id,
            "run_date": row.run_date,
            "status": row.status,
            "total_targets": row.total_targets,
            "total_processed": row.total_processed,
            "total_success": row.total_success,
            "total_failed": row.total_failed,
            "started_at": row.started_at,
            "finished_at": row.finished_at,
        }
        for row in rows
    ]


@router.get("/api/growth/competitor-scrape/snapshots", summary="List recent lightweight snapshots")
def list_recent_snapshots(
    user_id: UUID,
    run_id: UUID | None = None,
    limit: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    stmt = (
        select(CompetitorSnapshot)
        .join(ScrapeRun, ScrapeRun.id == CompetitorSnapshot.scrape_run_id)
        .where(ScrapeRun.user_id == user_id)
        .order_by(CompetitorSnapshot.created_at.desc())
        .limit(limit)
    )
    if run_id:
        stmt = stmt.where(CompetitorSnapshot.scrape_run_id == run_id)

    rows = db.scalars(stmt).all()
    return [
        {
            "id": row.id,
            "run_id": row.scrape_run_id,
            "competitor_id": row.competitor_id,
            "observed_on": row.observed_on,
            "rating_x100": row.rating_x100,
            "total_reviews": row.total_reviews,
            "price_bucket": row.price_bucket,
            "posts_30d": row.posts_30d,
            "source_status": row.source_status,
        }
        for row in rows
    ]
