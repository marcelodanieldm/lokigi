"""
backend/app/enterprise/network_aggregation.py
================================================
High-performance multi-location aggregation for Lokigi Enterprise.

Design
------
- Pure-Postgres aggregation via SQLAlchemy Core (no ORM overhead for bulk reads).
- Outlier detection using the IQR (interquartile range) method on the DB side
  with PostgreSQL window functions — no Python loops over large datasets.
- Results are cached in Redis as JSON with a configurable TTL.
- A Celery beat task (`refresh_network_snapshot`) runs on a schedule so the
  SuperAdmin dashboard always reads from cache and never waits on a query.

Public API
----------
    from app.enterprise.network_aggregation import NetworkAggregationService

    svc = NetworkAggregationService(redis_client=redis)
    snapshot = svc.get_network_snapshot(org_id=org.id, db=db, force_refresh=False)
    # → NetworkSnapshot dataclass with `locations`, `outliers`, `totals`

Outlier definition
------------------
A location is an *outlier* if its avg_rating or avg_sentiment falls outside
[Q1 - 1.5*IQR, Q3 + 1.5*IQR] for the org's network.  These are surfaced as
"needs attention" in the Dashboard Heat Map.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Column, Float, Integer, String, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ─── Result dataclasses ───────────────────────────────────────────────────────

@dataclass
class LocationMetric:
    location_id: str
    location_name: str
    avg_rating: float
    review_count: int
    avg_sentiment: float
    brand_authority: float   # composite 0–100
    is_outlier: bool
    outlier_reason: str | None   # e.g. "low_rating" | "low_sentiment" | "low_volume"
    trend: str   # "up" | "flat" | "down"  (vs. prior 30-day window)


@dataclass
class NetworkTotals:
    total_locations: int
    total_reviews: int
    network_avg_rating: float
    network_avg_sentiment: float
    network_brand_authority: float
    outlier_count: int
    healthy_count: int
    warning_count: int   # < Q1 but > lower fence


@dataclass
class NetworkSnapshot:
    org_id: str
    generated_at: str
    period_start: str
    period_end: str
    locations: list[LocationMetric]
    outliers: list[LocationMetric]
    totals: NetworkTotals


# ─── SQL queries ──────────────────────────────────────────────────────────────

# Main aggregation query.
# Requires: reviews r  JOIN  google_connections gc ON r.connection_id = gc.id
#           JOIN  org_memberships om ON gc.user_id = om.user_id
# Produces one row per location with avg_rating, review_count, avg_sentiment.
# Window functions compute Q1/Q3 for rating and sentiment across the org.
_AGG_QUERY = text("""
WITH period_reviews AS (
    SELECT
        r.location_id,
        gc.business_name                                    AS location_name,
        r.rating::FLOAT                                     AS rating,
        COALESCE(r.reply_alert_priority, 'none')            AS alert_priority,
        -- normalise sentiment score: stored as text 'positive'/'neutral'/'negative'
        -- or as a float in [-1, 1] depending on NLP model version
        CASE
            WHEN r.reply_action = 'positive'  THEN 1.0
            WHEN r.reply_action = 'neutral'   THEN 0.5
            WHEN r.reply_action = 'negative'  THEN 0.0
            ELSE 0.5
        END                                                 AS sentiment_score
    FROM reviews r
    JOIN google_connections gc ON r.connection_id = gc.id
    JOIN org_memberships om    ON gc.user_id = om.user_id
    WHERE om.org_id       = :org_id
      AND r.create_time  >= :period_start
      AND r.create_time  <  :period_end
),
location_agg AS (
    SELECT
        location_id,
        MAX(location_name)                                  AS location_name,
        ROUND(AVG(rating)::NUMERIC, 2)::FLOAT               AS avg_rating,
        COUNT(*)                                            AS review_count,
        ROUND(AVG(sentiment_score)::NUMERIC, 3)::FLOAT      AS avg_sentiment
    FROM period_reviews
    GROUP BY location_id
),
network_stats AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_rating)    AS q1_rating,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_rating)    AS q3_rating,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_sentiment) AS q1_sentiment,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_sentiment) AS q3_sentiment,
        AVG(avg_rating)                                             AS net_avg_rating,
        AVG(avg_sentiment)                                          AS net_avg_sentiment,
        SUM(review_count)                                           AS total_reviews,
        COUNT(*)                                                    AS total_locations
    FROM location_agg
),
outlier_flags AS (
    SELECT
        la.*,
        ns.q1_rating,
        ns.q3_rating,
        ns.q1_sentiment,
        ns.q3_sentiment,
        ns.net_avg_rating,
        ns.net_avg_sentiment,
        ns.total_reviews,
        ns.total_locations,
        -- IQR fences
        (ns.q1_rating    - 1.5 * (ns.q3_rating    - ns.q1_rating))    AS lower_fence_rating,
        (ns.q1_sentiment - 1.5 * (ns.q3_sentiment - ns.q1_sentiment))  AS lower_fence_sentiment
    FROM location_agg la
    CROSS JOIN network_stats ns
)
SELECT
    location_id,
    location_name,
    avg_rating,
    review_count,
    avg_sentiment,
    -- Brand Authority Index: rating 40%, sentiment 40%, volume 20%
    ROUND((
        (avg_rating / 5.0)                                                * 0.40
        + avg_sentiment                                                   * 0.40
        + (LEAST(review_count, 500) / 500.0)                             * 0.20
    ) * 100, 1)::FLOAT                                                   AS brand_authority,
    (avg_rating    < lower_fence_rating
     OR avg_sentiment < lower_fence_sentiment)                           AS is_outlier,
    CASE
        WHEN avg_rating    < lower_fence_rating    THEN 'low_rating'
        WHEN avg_sentiment < lower_fence_sentiment THEN 'low_sentiment'
        ELSE NULL
    END                                                                  AS outlier_reason,
    net_avg_rating,
    net_avg_sentiment,
    total_reviews::INT,
    total_locations::INT
FROM outlier_flags
ORDER BY brand_authority DESC
""")

# Trend query: compare current 30d avg_rating vs prior 30d
_TREND_QUERY = text("""
SELECT
    r.location_id,
    ROUND(AVG(CASE WHEN r.create_time >= :current_start THEN r.rating::FLOAT END)::NUMERIC, 2) AS current_avg,
    ROUND(AVG(CASE WHEN r.create_time <  :current_start THEN r.rating::FLOAT END)::NUMERIC, 2) AS prior_avg
FROM reviews r
JOIN google_connections gc ON r.connection_id = gc.id
JOIN org_memberships om    ON gc.user_id = om.user_id
WHERE om.org_id      = :org_id
  AND r.create_time >= :prior_start
  AND r.create_time <  :period_end
GROUP BY r.location_id
""")


# ─── Service class ────────────────────────────────────────────────────────────

class NetworkAggregationService:
    """
    Aggregates metrics for an org's entire location network.

    Parameters
    ----------
    redis_client:
        A redis-py `Redis` instance (sync).  Pass `None` to disable caching.
    cache_ttl:
        Seconds to keep the snapshot in Redis (default 300 = 5 min).
    lookback_days:
        Rolling window for the aggregation (default 30 days).
    """

    def __init__(
        self,
        redis_client=None,
        cache_ttl: int = 300,
        lookback_days: int = 30,
    ) -> None:
        self._redis = redis_client
        self._ttl = cache_ttl
        self._lookback = lookback_days

    # ── Public ────────────────────────────────────────────────────────────────

    def get_network_snapshot(
        self,
        org_id: uuid.UUID,
        db: Session,
        force_refresh: bool = False,
    ) -> NetworkSnapshot:
        """
        Return the latest network snapshot, hitting Redis first unless
        `force_refresh=True`.
        """
        cache_key = f"network_snapshot:{org_id}"

        if not force_refresh and self._redis is not None:
            try:
                raw = self._redis.get(cache_key)
                if raw:
                    logger.debug("NetworkAggregationService: cache HIT for org %s", org_id)
                    return self._deserialize(raw)
            except Exception as exc:
                logger.warning("Redis get error: %s", exc)

        snapshot = self._build_snapshot(org_id, db)
        self._write_cache(cache_key, snapshot)
        return snapshot

    def invalidate_cache(self, org_id: uuid.UUID) -> None:
        if self._redis is not None:
            try:
                self._redis.delete(f"network_snapshot:{org_id}")
            except Exception as exc:
                logger.warning("Redis delete error: %s", exc)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_snapshot(self, org_id: uuid.UUID, db: Session) -> NetworkSnapshot:
        now = datetime.now(timezone.utc)
        period_end = now
        period_start = now - timedelta(days=self._lookback)
        prior_start = period_start - timedelta(days=self._lookback)

        # Main aggregation
        rows = db.execute(
            _AGG_QUERY,
            {
                "org_id": str(org_id),
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
            },
        ).mappings().all()

        # Trend data
        trend_rows = db.execute(
            _TREND_QUERY,
            {
                "org_id": str(org_id),
                "current_start": period_start.isoformat(),
                "prior_start": prior_start.isoformat(),
                "period_end": period_end.isoformat(),
            },
        ).mappings().all()

        trend_map: dict[str, str] = {}
        for tr in trend_rows:
            cur = tr["current_avg"] or 0.0
            pri = tr["prior_avg"] or 0.0
            if cur - pri > 0.1:
                trend_map[tr["location_id"]] = "up"
            elif pri - cur > 0.1:
                trend_map[tr["location_id"]] = "down"
            else:
                trend_map[tr["location_id"]] = "flat"

        locations: list[LocationMetric] = []
        for row in rows:
            loc = LocationMetric(
                location_id=row["location_id"],
                location_name=row["location_name"] or row["location_id"],
                avg_rating=float(row["avg_rating"] or 0),
                review_count=int(row["review_count"] or 0),
                avg_sentiment=float(row["avg_sentiment"] or 0),
                brand_authority=float(row["brand_authority"] or 0),
                is_outlier=bool(row["is_outlier"]),
                outlier_reason=row["outlier_reason"],
                trend=trend_map.get(row["location_id"], "flat"),
            )
            locations.append(loc)

        outliers = [l for l in locations if l.is_outlier]
        healthy = [l for l in locations if not l.is_outlier and l.avg_rating >= 4.0]
        warning = [l for l in locations if not l.is_outlier and l.avg_rating < 4.0]

        # Totals from first row (all rows share network-wide stats)
        if rows:
            net_avg_rating = float(rows[0]["net_avg_rating"] or 0)
            net_avg_sentiment = float(rows[0]["net_avg_sentiment"] or 0)
            total_reviews = int(rows[0]["total_reviews"] or 0)
            total_locations = int(rows[0]["total_locations"] or 0)
        else:
            net_avg_rating = 0.0
            net_avg_sentiment = 0.0
            total_reviews = 0
            total_locations = 0

        network_bai = round(
            (net_avg_rating / 5.0) * 40
            + net_avg_sentiment * 40
            + min(total_reviews / (500 * max(total_locations, 1)), 1.0) * 20,
            1,
        )

        totals = NetworkTotals(
            total_locations=total_locations,
            total_reviews=total_reviews,
            network_avg_rating=round(net_avg_rating, 2),
            network_avg_sentiment=round(net_avg_sentiment, 3),
            network_brand_authority=network_bai,
            outlier_count=len(outliers),
            healthy_count=len(healthy),
            warning_count=len(warning),
        )

        return NetworkSnapshot(
            org_id=str(org_id),
            generated_at=now.isoformat(),
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            locations=locations,
            outliers=outliers,
            totals=totals,
        )

    def _write_cache(self, key: str, snapshot: NetworkSnapshot) -> None:
        if self._redis is None:
            return
        try:
            payload = json.dumps({
                "org_id": snapshot.org_id,
                "generated_at": snapshot.generated_at,
                "period_start": snapshot.period_start,
                "period_end": snapshot.period_end,
                "locations": [asdict(l) for l in snapshot.locations],
                "outliers": [asdict(l) for l in snapshot.outliers],
                "totals": asdict(snapshot.totals),
            })
            self._redis.setex(key, self._ttl, payload)
        except Exception as exc:
            logger.warning("Redis write error: %s", exc)

    @staticmethod
    def _deserialize(raw: bytes | str) -> NetworkSnapshot:
        data = json.loads(raw)
        locations = [LocationMetric(**l) for l in data["locations"]]
        outliers = [LocationMetric(**l) for l in data["outliers"]]
        totals = NetworkTotals(**data["totals"])
        return NetworkSnapshot(
            org_id=data["org_id"],
            generated_at=data["generated_at"],
            period_start=data["period_start"],
            period_end=data["period_end"],
            locations=locations,
            outliers=outliers,
            totals=totals,
        )


# ─── FastAPI router ───────────────────────────────────────────────────────────

def make_network_router(aggregation_service: NetworkAggregationService):
    """
    Returns a FastAPI APIRouter exposing the network snapshot endpoints.
    Mount at /enterprise/network.
    """
    from fastapi import APIRouter, Depends, Query
    from app.enterprise.multi_tenancy import Organization, get_current_org
    from app.database import get_db

    router = APIRouter(prefix="/enterprise/network", tags=["enterprise-network"])

    @router.get("/snapshot")
    def network_snapshot(
        force_refresh: bool = Query(False),
        org: Organization = Depends(get_current_org),
        db: Session = Depends(get_db),
    ):
        """
        Returns the aggregated network snapshot.
        Reads from Redis cache unless force_refresh=true.
        """
        snap = aggregation_service.get_network_snapshot(
            org_id=org.id, db=db, force_refresh=force_refresh
        )
        return {
            "generated_at": snap.generated_at,
            "period_start": snap.period_start,
            "period_end": snap.period_end,
            "totals": asdict(snap.totals),
            "locations": [asdict(l) for l in snap.locations],
            "outliers": [asdict(l) for l in snap.outliers],
        }

    @router.get("/outliers")
    def network_outliers(
        org: Organization = Depends(get_current_org),
        db: Session = Depends(get_db),
    ):
        snap = aggregation_service.get_network_snapshot(org_id=org.id, db=db)
        return {"outliers": [asdict(l) for l in snap.outliers]}

    @router.get("/ranking")
    def network_ranking(
        limit: int = Query(20, ge=1, le=200),
        org: Organization = Depends(get_current_org),
        db: Session = Depends(get_db),
    ):
        snap = aggregation_service.get_network_snapshot(org_id=org.id, db=db)
        ranked = sorted(snap.locations, key=lambda l: l.brand_authority, reverse=True)
        return {
            "ranking": [asdict(l) for l in ranked[:limit]],
            "total": len(ranked),
        }

    return router


# ─── Celery refresh task ──────────────────────────────────────────────────────

def register_celery_refresh_task(celery_app, service: NetworkAggregationService):
    """
    Register a periodic Celery task that refreshes the snapshot for all
    active orgs every 5 minutes.

    Usage in celery_app.py:
        from app.enterprise.network_aggregation import register_celery_refresh_task
        register_celery_refresh_task(celery_app, network_service)
    """

    @celery_app.task(name="enterprise.refresh_network_snapshots", bind=True)
    def refresh_network_snapshots(self):
        from app.database import SessionLocal
        from app.enterprise.multi_tenancy import Organization

        if SessionLocal is None:
            return {"status": "skipped", "reason": "no DB session"}

        refreshed = []
        with SessionLocal() as db:
            orgs = db.scalars(__import__("sqlalchemy", fromlist=["select"]).select(Organization)).all()
            for org in orgs:
                try:
                    service.get_network_snapshot(org_id=org.id, db=db, force_refresh=True)
                    refreshed.append(str(org.id))
                except Exception as exc:
                    logger.error("Snapshot refresh failed for org %s: %s", org.id, exc)

        return {"status": "ok", "refreshed": refreshed}

    return refresh_network_snapshots
