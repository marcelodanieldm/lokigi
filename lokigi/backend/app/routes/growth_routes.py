"""Growth plan endpoints for competitor intelligence baseline management."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.growth_premium_report_service import GrowthPremiumReportService, PremiumConfig
from app.growth_sentiment_benchmark_service import BenchmarkConfig, GrowthSentimentBenchmarkService
from app.growth_scraper_service import GrowthScraperService
from app.models import (
    GrowthBenchmarkComparison,
    GrowthCompetitor,
    GrowthCompetitorKeywordMetric,
    GrowthSentimentBenchmarkRun,
    GrowthSentimentBenchmarkTopicGap,
    GrowthCompetitorServiceSnapshot,
    GrowthCompetitorSnapshot,
    GrowthKeywordConquestEvent,
    GrowthSerpObservation,
    User,
)

router = APIRouter(prefix="/api/growth", tags=["growth"])


class GrowthCompetitorCreateRequest(BaseModel):
    user_id: UUID
    name: str = Field(min_length=2, max_length=255)
    google_place_id: str = Field(min_length=5, max_length=128)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = Field(default=None, min_length=2, max_length=120)


class GrowthCompetitorResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    google_place_id: str
    country_code: str | None = None
    city: str | None = None
    is_active: bool
    created_at: datetime


class GrowthBenchmarkRow(BaseModel):
    competitor_id: UUID
    competitor_name: str
    observed_at: datetime
    rating_gap: float | None = None
    review_count_gap: int | None = None
    review_growth_30d_gap: int | None = None
    posting_freq_30d_gap: int | None = None
    keyword_share_gap: float | None = None


class GrowthCompetitorLatestResponse(BaseModel):
    competitor_id: UUID
    competitor_name: str
    latest_snapshot: dict
    services: list[str]
    top_keywords: list[dict]


class GrowthScrapeCompetitorRequest(BaseModel):
    user_id: UUID
    include_benchmark: bool = True
    client_google_place_id: str | None = Field(default=None, min_length=5, max_length=128)


class GrowthScrapeBulkRequest(BaseModel):
    user_id: UUID
    include_benchmark: bool = True
    client_google_place_id: str | None = Field(default=None, min_length=5, max_length=128)


class GrowthSentimentBenchmarkRunRequest(BaseModel):
    user_id: UUID
    time_window_days: int = Field(default=30, ge=7, le=120)
    min_support_topic_competitors: int = Field(default=30, ge=5, le=500)
    opp_threshold_competitor_complaint_rate: float = Field(default=0.35, ge=0, le=1)
    opp_threshold_client_complaint_rate: float = Field(default=0.15, ge=0, le=1)
    confidence_threshold: float = Field(default=0.70, ge=0, le=1)
    top_marketing_opportunities: int = Field(default=8, ge=1, le=20)


class GrowthSerpObservationItem(BaseModel):
    keyword: str = Field(min_length=2, max_length=120)
    location_label: str = Field(default="default", min_length=2, max_length=140)
    entity_type: str = Field(default="client", pattern="^(client|competitor)$")
    rank_position: int = Field(ge=1, le=30)
    observed_at: datetime
    competitor_id: UUID | None = None


class GrowthSerpObservationIngestRequest(BaseModel):
    user_id: UUID
    observations: list[GrowthSerpObservationItem] = Field(min_length=1, max_length=500)


class GrowthKeywordConquestItem(BaseModel):
    keyword: str = Field(min_length=2, max_length=120)
    location_label: str = Field(default="default", min_length=2, max_length=140)
    conquered_at: datetime
    displaced_competitor_id: UUID | None = None
    previous_rank: int | None = Field(default=None, ge=1, le=30)
    new_rank: int | None = Field(default=None, ge=1, le=30)


class GrowthKeywordConquestIngestRequest(BaseModel):
    user_id: UUID
    events: list[GrowthKeywordConquestItem] = Field(min_length=1, max_length=200)


@router.post(
    "/competitors",
    response_model=GrowthCompetitorResponse,
    summary="Create Growth competitor target",
)
def create_growth_competitor(
    request: GrowthCompetitorCreateRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = db.scalars(
        select(GrowthCompetitor).where(
            GrowthCompetitor.user_id == request.user_id,
            GrowthCompetitor.google_place_id == request.google_place_id,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Competitor already exists for this user",
        )

    competitor = GrowthCompetitor(
        user_id=request.user_id,
        name=request.name.strip(),
        google_place_id=request.google_place_id.strip(),
        country_code=request.country_code.upper().strip() if request.country_code else None,
        city=request.city.strip() if request.city else None,
        is_active=True,
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


@router.get(
    "/competitors",
    response_model=list[GrowthCompetitorResponse],
    summary="List user competitors",
)
def list_growth_competitors(
    user_id: UUID,
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    stmt = select(GrowthCompetitor).where(GrowthCompetitor.user_id == user_id)
    if not include_inactive:
        stmt = stmt.where(GrowthCompetitor.is_active.is_(True))

    rows = db.scalars(stmt.order_by(GrowthCompetitor.created_at.desc())).all()
    return list(rows)


@router.delete(
    "/competitors/{competitor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete competitor target",
)
def deactivate_growth_competitor(
    competitor_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    competitor = db.get(GrowthCompetitor, competitor_id)
    if not competitor or competitor.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    competitor.is_active = False
    competitor.updated_at = datetime.utcnow()
    db.add(competitor)
    db.commit()
    return None


@router.get(
    "/benchmark/latest",
    response_model=list[GrowthBenchmarkRow],
    summary="Read latest benchmark comparison rows",
)
def get_growth_benchmark_latest(
    user_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    rows = db.execute(
        select(GrowthBenchmarkComparison, GrowthCompetitor.name)
        .join(GrowthCompetitor, GrowthCompetitor.id == GrowthBenchmarkComparison.competitor_id)
        .where(GrowthBenchmarkComparison.user_id == user_id)
        .order_by(desc(GrowthBenchmarkComparison.observed_at))
        .limit(limit)
    ).all()

    return [
        GrowthBenchmarkRow(
            competitor_id=row[0].competitor_id,
            competitor_name=row[1],
            observed_at=row[0].observed_at,
            rating_gap=float(row[0].rating_gap) if row[0].rating_gap is not None else None,
            review_count_gap=row[0].review_count_gap,
            review_growth_30d_gap=row[0].review_growth_30d_gap,
            posting_freq_30d_gap=row[0].posting_freq_30d_gap,
            keyword_share_gap=float(row[0].keyword_share_gap) if row[0].keyword_share_gap is not None else None,
        )
        for row in rows
    ]


@router.get(
    "/competitors/{competitor_id}/latest",
    response_model=GrowthCompetitorLatestResponse,
    summary="Get latest scraped state for one competitor",
)
def get_growth_competitor_latest(
    competitor_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    competitor = db.get(GrowthCompetitor, competitor_id)
    if not competitor or competitor.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    snapshot = db.scalars(
        select(GrowthCompetitorSnapshot)
        .where(GrowthCompetitorSnapshot.competitor_id == competitor_id)
        .order_by(desc(GrowthCompetitorSnapshot.observed_at))
        .limit(1)
    ).first()

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No snapshots found for competitor",
        )

    services_rows = db.scalars(
        select(GrowthCompetitorServiceSnapshot.service_name_normalized)
        .where(
            and_(
                GrowthCompetitorServiceSnapshot.competitor_id == competitor_id,
                GrowthCompetitorServiceSnapshot.observed_at == snapshot.observed_at,
            )
        )
        .order_by(GrowthCompetitorServiceSnapshot.service_name_normalized.asc())
    ).all()

    period_end = snapshot.observed_at.date()
    period_start = period_end - date.resolution * 29
    keyword_rows = db.scalars(
        select(GrowthCompetitorKeywordMetric)
        .where(
            GrowthCompetitorKeywordMetric.competitor_id == competitor_id,
            GrowthCompetitorKeywordMetric.period_start == period_start,
            GrowthCompetitorKeywordMetric.period_end == period_end,
        )
        .order_by(desc(GrowthCompetitorKeywordMetric.mentions_count))
        .limit(10)
    ).all()

    return GrowthCompetitorLatestResponse(
        competitor_id=competitor.id,
        competitor_name=competitor.name,
        latest_snapshot={
            "observed_at": snapshot.observed_at,
            "review_count_total": snapshot.review_count_total,
            "rating_avg": float(snapshot.rating_avg) if snapshot.rating_avg is not None else None,
            "posts_count_7d": snapshot.posts_count_7d,
            "posts_count_30d": snapshot.posts_count_30d,
            "services_count": snapshot.services_count,
            "data_source": snapshot.data_source,
        },
        services=list(services_rows),
        top_keywords=[
            {
                "keyword": row.keyword,
                "mentions_count": row.mentions_count,
                "sentiment_positive_pct": float(row.sentiment_positive_pct)
                if row.sentiment_positive_pct is not None
                else None,
                "sentiment_neutral_pct": float(row.sentiment_neutral_pct)
                if row.sentiment_neutral_pct is not None
                else None,
                "sentiment_negative_pct": float(row.sentiment_negative_pct)
                if row.sentiment_negative_pct is not None
                else None,
            }
            for row in keyword_rows
        ],
    )


@router.post(
    "/competitors/{competitor_id}/scrape",
    summary="Run Python Playwright scrape for one competitor",
)
def scrape_growth_competitor(
    competitor_id: UUID,
    request: GrowthScrapeCompetitorRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthScraperService(db)
    try:
        result = service.scrape_and_persist_competitor(
            user_id=request.user_id,
            competitor_id=competitor_id,
            include_benchmark=request.include_benchmark,
            client_google_place_id=request.client_google_place_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Scrape failed: {exc}") from exc

    return {"ok": True, "result": result}


@router.post(
    "/scrape/run",
    summary="Run Python Playwright scrape for all active competitors",
)
def scrape_growth_all(
    request: GrowthScrapeBulkRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthScraperService(db)
    try:
        result = service.scrape_and_persist_all_competitors(
            user_id=request.user_id,
            include_benchmark=request.include_benchmark,
            client_google_place_id=request.client_google_place_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Scrape batch failed: {exc}") from exc

    return {"ok": True, **result}


@router.post(
    "/sentiment-benchmark/run",
    summary="Run NLP sentiment benchmark and persist results",
)
def run_growth_sentiment_benchmark(
    request: GrowthSentimentBenchmarkRunRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthSentimentBenchmarkService(db)
    cfg = BenchmarkConfig(
        time_window_days=request.time_window_days,
        min_support_topic_competitors=request.min_support_topic_competitors,
        opp_threshold_competitor_complaint_rate=request.opp_threshold_competitor_complaint_rate,
        opp_threshold_client_complaint_rate=request.opp_threshold_client_complaint_rate,
        confidence_threshold=request.confidence_threshold,
        top_marketing_opportunities=request.top_marketing_opportunities,
    )
    try:
        result = service.run_for_user(user_id=request.user_id, config=cfg)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Sentiment benchmark failed: {exc}",
        ) from exc

    return {"ok": True, "result": result}


@router.get(
    "/sentiment-benchmark/latest",
    summary="Get latest persisted sentiment benchmark run",
)
def get_latest_growth_sentiment_benchmark(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    run = db.scalars(
        select(GrowthSentimentBenchmarkRun)
        .where(GrowthSentimentBenchmarkRun.user_id == user_id)
        .order_by(desc(GrowthSentimentBenchmarkRun.created_at))
        .limit(1)
    ).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No benchmark run found")

    return {
        "id": str(run.id),
        "status": run.status,
        "window_days": run.window_days,
        "client_sentiment_score": float(run.client_sentiment_score)
        if run.client_sentiment_score is not None
        else None,
        "competitor_average_sentiment_score": float(run.competitor_average_sentiment_score)
        if run.competitor_average_sentiment_score is not None
        else None,
        "client_negative_rate": float(run.client_negative_rate) if run.client_negative_rate is not None else None,
        "rank_client_among_6": run.rank_client_among_6,
        "summary_payload": run.summary_payload,
        "diagnostics_payload": run.diagnostics_payload,
        "created_at": run.created_at,
    }


@router.get(
    "/sentiment-benchmark/runs",
    summary="List persisted sentiment benchmark runs",
)
def list_growth_sentiment_benchmark_runs(
    user_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    rows = db.scalars(
        select(GrowthSentimentBenchmarkRun)
        .where(GrowthSentimentBenchmarkRun.user_id == user_id)
        .order_by(desc(GrowthSentimentBenchmarkRun.created_at))
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "items": [
            {
                "id": str(row.id),
                "status": row.status,
                "window_days": row.window_days,
                "client_sentiment_score": float(row.client_sentiment_score)
                if row.client_sentiment_score is not None
                else None,
                "competitor_average_sentiment_score": float(row.competitor_average_sentiment_score)
                if row.competitor_average_sentiment_score is not None
                else None,
                "client_negative_rate": float(row.client_negative_rate)
                if row.client_negative_rate is not None
                else None,
                "rank_client_among_6": row.rank_client_among_6,
                "created_at": row.created_at,
            }
            for row in rows
        ],
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/sentiment-benchmark/runs/{run_id}",
    summary="Get one persisted sentiment benchmark run with topic gaps",
)
def get_growth_sentiment_benchmark_run_detail(
    run_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    run = db.get(GrowthSentimentBenchmarkRun, run_id)
    if not run or run.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark run not found")

    gaps = db.scalars(
        select(GrowthSentimentBenchmarkTopicGap)
        .where(GrowthSentimentBenchmarkTopicGap.run_id == run.id)
        .order_by(
            GrowthSentimentBenchmarkTopicGap.label.asc(),
            desc(GrowthSentimentBenchmarkTopicGap.gap),
        )
    ).all()

    return {
        "run": {
            "id": str(run.id),
            "status": run.status,
            "window_days": run.window_days,
            "client_sentiment_score": float(run.client_sentiment_score)
            if run.client_sentiment_score is not None
            else None,
            "competitor_average_sentiment_score": float(run.competitor_average_sentiment_score)
            if run.competitor_average_sentiment_score is not None
            else None,
            "client_negative_rate": float(run.client_negative_rate)
            if run.client_negative_rate is not None
            else None,
            "rank_client_among_6": run.rank_client_among_6,
            "summary_payload": run.summary_payload,
            "diagnostics_payload": run.diagnostics_payload,
            "created_at": run.created_at,
        },
        "topic_gaps": [
            {
                "id": str(g.id),
                "topic": g.topic,
                "client_complaint_rate": float(g.client_complaint_rate)
                if g.client_complaint_rate is not None
                else None,
                "competitor_complaint_rate": float(g.competitor_complaint_rate)
                if g.competitor_complaint_rate is not None
                else None,
                "gap": float(g.gap) if g.gap is not None else None,
                "support_competitors": g.support_competitors,
                "label": g.label,
                "confidence": float(g.confidence) if g.confidence is not None else None,
                "evidence_payload": g.evidence_payload,
            }
            for g in gaps
        ],
    }


@router.post(
    "/serp-observations",
    summary="Ingest SERP observations for advanced Growth KPIs",
)
def ingest_growth_serp_observations(
    request: GrowthSerpObservationIngestRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    inserted = 0
    for item in request.observations:
        if item.entity_type == "competitor" and item.competitor_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="competitor_id is required when entity_type is competitor",
            )

        row = GrowthSerpObservation(
            user_id=request.user_id,
            competitor_id=item.competitor_id,
            keyword=item.keyword.strip().lower(),
            location_label=item.location_label.strip().lower(),
            entity_type=item.entity_type,
            rank_position=item.rank_position,
            observed_at=item.observed_at,
        )
        db.add(row)
        inserted += 1

    db.commit()
    return {"ok": True, "inserted": inserted}


@router.post(
    "/keyword-conquests",
    summary="Ingest keyword conquest events for Growth KPI tracking",
)
def ingest_growth_keyword_conquests(
    request: GrowthKeywordConquestIngestRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    inserted = 0
    for item in request.events:
        row = GrowthKeywordConquestEvent(
            user_id=request.user_id,
            keyword=item.keyword.strip().lower(),
            location_label=item.location_label.strip().lower(),
            conquered_at=item.conquered_at,
            displaced_competitor_id=item.displaced_competitor_id,
            previous_rank=item.previous_rank,
            new_rank=item.new_rank,
        )
        db.add(row)
        inserted += 1

    db.commit()
    return {"ok": True, "inserted": inserted}


@router.get(
    "/premium-report",
    summary="Build Growth Premium strategic report payload",
)
def get_growth_premium_report(
    user_id: UUID,
    window_days: int = Query(default=30, ge=7, le=120),
    max_locations: int = Query(default=5, ge=1, le=5),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthPremiumReportService(db)
    payload = service.build_report(
        user_id=user_id,
        config=PremiumConfig(window_days=window_days, max_locations=max_locations),
    )
    return {"ok": True, "user_id": str(user_id), "report": payload}
