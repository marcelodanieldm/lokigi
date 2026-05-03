"""local_scout_service.py — Local Scout: Playwright scraper + Sentiment Delta.

Responsibilities
────────────────
1. ``LocalScoutScraper``   — uses Playwright to visit a Google Maps URL every 48 h
   and extract: average rating, total review count, date of last post.

2. ``SentimentDeltaService`` — computes the five-axis Positioning Radar comparing
   the client (their own review data) against up to 5 scraped competitors.
   Returns a JSON-serialisable dict ready for Chart.js radar / spider chart.

Radar axes (each scored 0 – 100)
──────────────────────────────────
  - reputacion  : weighted rating comparison (client vs rival avg)
  - actividad   : post recency – how recent is the last Google post?
  - volumen     : review count momentum (ratio client/max-rival, capped)
  - velocidad   : response-rate proxy from PendingResponse table
  - tendencia   : 30-day delta in avg rating vs prior 30 days
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    CompetitorEntity,
    CompetitorHistory,
    GoogleConnection,
    PendingResponse,
    Review,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Playwright scraper
# ──────────────────────────────────────────────────────────────────────────────

_RATING_RE = re.compile(r"([1-5][.,][0-9])")
_REVIEW_COUNT_RE = re.compile(r"([\d,\.]+)\s*(?:reviews?|reseñas?|opiniones?)", re.IGNORECASE)
_POST_DATE_RE = re.compile(
    r"(\d{1,2})\s+(?:de\s+)?(enero|febrero|marzo|abril|mayo|junio|julio|agosto|"
    r"septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(\d{4})",
    re.IGNORECASE,
)
_MONTH_MAP = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def _parse_rating(text: str) -> float | None:
    m = _RATING_RE.search(text)
    if m:
        raw = m.group(1).replace(",", ".")
        val = float(raw)
        return val if 0 <= val <= 5 else None
    return None


def _parse_review_count(text: str) -> int | None:
    m = _REVIEW_COUNT_RE.search(text)
    if m:
        raw = m.group(1).replace(",", "").replace(".", "")
        try:
            return int(raw)
        except ValueError:
            return None
    return None


def _parse_last_post_date(text: str) -> date | None:
    m = _POST_DATE_RE.search(text)
    if m:
        day = int(m.group(1))
        month = _MONTH_MAP.get(m.group(2).lower(), 0)
        year = int(m.group(3))
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                pass
    return None


async def _scrape_google_maps_url(url: str, timeout_ms: int = 30_000) -> dict[str, Any]:
    """Visit a Google Maps business URL with Playwright and extract metrics."""
    from playwright.async_api import async_playwright, TimeoutError as PWTimeout

    result: dict[str, Any] = {
        "rating_avg": None,
        "review_count": None,
        "last_post_date": None,
        "scrape_status": "error",
    }

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="es-ES",
            )
            page = await ctx.new_page()
            try:
                await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                await page.wait_for_timeout(2500)
                page_text = await page.inner_text("body")

                result["rating_avg"] = _parse_rating(page_text)
                result["review_count"] = _parse_review_count(page_text)
                result["last_post_date"] = _parse_last_post_date(page_text)
                result["scrape_status"] = (
                    "ok" if result["rating_avg"] is not None else "partial"
                )
            except PWTimeout:
                result["scrape_status"] = "blocked"
            finally:
                await browser.close()
    except Exception as exc:
        logger.warning("LocalScout scrape failed for %s: %s", url, exc)
        result["scrape_status"] = "error"

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator  – called by the Celery beat task
# ──────────────────────────────────────────────────────────────────────────────


class LocalScoutOrchestrator:
    """Runs the 48-h competitor scrape for every user who has active competitors."""

    MAX_COMPETITORS_PER_USER = 5

    def __init__(self, db: Session) -> None:
        self.db = db

    def run_all_users(self) -> dict[str, int]:
        users_processed = 0
        total_scraped = 0
        total_failed = 0

        # Fetch distinct users with at least one active competitor
        user_ids_result = self.db.execute(
            select(CompetitorEntity.user_id)
            .where(CompetitorEntity.status == "active")
            .distinct()
        ).scalars().all()

        for user_id in user_ids_result:
            try:
                result = self.run_for_user(user_id)
                total_scraped += result["scraped"]
                total_failed += result["failed"]
                users_processed += 1
            except Exception:
                logger.exception("LocalScout failed for user_id=%s", user_id)
                total_failed += 1

        return {
            "users_processed": users_processed,
            "total_scraped": total_scraped,
            "total_failed": total_failed,
        }

    def run_for_user(self, user_id: UUID) -> dict[str, int]:
        competitors = self.db.execute(
            select(CompetitorEntity)
            .where(CompetitorEntity.user_id == user_id, CompetitorEntity.status == "active")
            .limit(self.MAX_COMPETITORS_PER_USER)
        ).scalars().all()

        scraped = 0
        failed = 0
        now = datetime.now(timezone.utc)

        for comp in competitors:
            try:
                raw = asyncio.run(_scrape_google_maps_url(
                    comp.maps_url,
                    timeout_ms=settings.growth_playwright_timeout_ms,
                ))
                entry = CompetitorHistory(
                    user_id=user_id,
                    competitor_id=comp.id,
                    scraped_at=now,
                    rating_avg=raw["rating_avg"],
                    review_count=raw["review_count"],
                    last_post_date=raw["last_post_date"],
                    scrape_status=raw["scrape_status"],
                )
                self.db.add(entry)
                scraped += 1
            except Exception:
                logger.exception("Scrape failed for competitor_id=%s", comp.id)
                failed += 1

        self.db.commit()
        return {"scraped": scraped, "failed": failed}


# ──────────────────────────────────────────────────────────────────────────────
# Sentiment Delta & Positioning Radar
# ──────────────────────────────────────────────────────────────────────────────


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def _rating_to_score(client: float | None, rivals: list[float]) -> float:
    """Convert absolute rating into a 0-100 positioning score."""
    if client is None:
        return 50.0
    if not rivals:
        return _clamp((client / 5.0) * 100)
    rival_avg = sum(rivals) / len(rivals)
    diff = client - rival_avg  # –5 … +5
    return _clamp(50.0 + diff * 12.0)  # ±1 star ≈ ±12 pts


def _post_recency_score(last_post: date | None) -> float:
    """Posts in last 7d → 100, 30d → 70, 90d → 40, older → 10."""
    if last_post is None:
        return 30.0
    age_days = (date.today() - last_post).days
    if age_days <= 7:
        return 100.0
    if age_days <= 30:
        return 70.0
    if age_days <= 90:
        return 45.0
    return 10.0


def _volume_score(client_count: int, rival_counts: list[int]) -> float:
    if not rival_counts:
        return 60.0
    max_rival = max(rival_counts) or 1
    ratio = client_count / max_rival
    return _clamp(ratio * 80)  # 80 when equal; 100 means client has 25 % more


def _response_rate_score(db: Session, user_id: UUID) -> float:
    """Use PendingResponse.status to approximate response rate (0-100)."""
    total = db.scalar(
        select(func.count(PendingResponse.id))
        .join(Review, Review.id == PendingResponse.review_pk)
        .join(
            __import__("app.models", fromlist=["GoogleConnection"]).GoogleConnection,
            __import__("app.models", fromlist=["GoogleConnection"]).GoogleConnection.id == Review.connection_id,
        )
        .where(
            __import__("app.models", fromlist=["GoogleConnection"]).GoogleConnection.user_id == user_id
        )
    ) or 0
    approved = db.scalar(
        select(func.count(PendingResponse.id))
        .join(Review, Review.id == PendingResponse.review_pk)
        .join(
            __import__("app.models", fromlist=["GoogleConnection"]).GoogleConnection,
            __import__("app.models", fromlist=["GoogleConnection"]).GoogleConnection.id == Review.connection_id,
        )
        .where(
            __import__("app.models", fromlist=["GoogleConnection"]).GoogleConnection.user_id == user_id,
            PendingResponse.status.in_(["approved", "sent"]),
        )
    ) or 0
    if total == 0:
        return 50.0
    return _clamp((approved / total) * 100)


def _trend_score(db: Session, connection_id: UUID) -> float:
    """Compare last-30d avg rating vs prior-30d avg rating."""
    now = datetime.now(timezone.utc)
    cutoff_30 = now - timedelta(days=30)
    cutoff_60 = now - timedelta(days=60)

    def _avg(start: datetime, end: datetime) -> float | None:
        val = db.scalar(
            select(func.avg(Review.rating))
            .where(
                Review.connection_id == connection_id,
                Review.create_time >= start,
                Review.create_time < end,
                Review.rating.isnot(None),
            )
        )
        return float(val) if val is not None else None

    recent = _avg(cutoff_30, now)
    prior = _avg(cutoff_60, cutoff_30)
    if recent is None:
        return 50.0
    if prior is None:
        return _clamp((recent / 5.0) * 100)
    delta = recent - prior  # –5 … +5
    return _clamp(50.0 + delta * 15.0)


class SentimentDeltaService:
    """Compute the 5-axis Positioning Radar for a user."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def compute_radar(self, user_id: UUID) -> dict[str, Any]:
        """Return a dict ready for the Chart.js radar dataset."""
        connection: GoogleConnection | None = self.db.scalar(
            select(GoogleConnection).where(GoogleConnection.user_id == user_id)
        )

        # ── Client metrics ─────────────────────────────────────────────────
        client_rating: float | None = None
        client_reviews: int = 0
        if connection:
            client_rating = self.db.scalar(
                select(func.avg(Review.rating)).where(
                    Review.connection_id == connection.id,
                    Review.rating.isnot(None),
                )
            )
            if client_rating is not None:
                client_rating = float(client_rating)
            count_val = self.db.scalar(
                select(func.count(Review.id)).where(Review.connection_id == connection.id)
            )
            client_reviews = int(count_val or 0)

        # ── Competitor latest history entries ──────────────────────────────
        subq = (
            select(
                CompetitorHistory.competitor_id,
                func.max(CompetitorHistory.scraped_at).label("latest"),
            )
            .where(CompetitorHistory.user_id == user_id)
            .group_by(CompetitorHistory.competitor_id)
            .subquery()
        )
        rival_rows = self.db.execute(
            select(CompetitorHistory).join(
                subq,
                (CompetitorHistory.competitor_id == subq.c.competitor_id)
                & (CompetitorHistory.scraped_at == subq.c.latest),
            )
        ).scalars().all()

        rival_ratings = [r.rating_avg for r in rival_rows if r.rating_avg is not None]
        rival_counts = [r.review_count for r in rival_rows if r.review_count is not None]

        # Best (most recent) competitor post date
        best_rival_post = max(
            (r.last_post_date for r in rival_rows if r.last_post_date),
            default=None,
        )

        # ── Axis scores ────────────────────────────────────────────────────
        reputacion = _rating_to_score(client_rating, rival_ratings)
        actividad = _post_recency_score(best_rival_post)  # placeholder; client post not tracked yet
        volumen = _volume_score(client_reviews, rival_counts)
        velocidad = _response_rate_score(self.db, user_id)
        tendencia = _trend_score(self.db, connection.id) if connection else 50.0

        axes = {
            "Reputación": round(reputacion, 1),
            "Actividad": round(actividad, 1),
            "Volumen": round(volumen, 1),
            "Velocidad": round(velocidad, 1),
            "Tendencia": round(tendencia, 1),
        }

        # ── Rival datasets (one per competitor) ───────────────────────────
        rivals_data: list[dict[str, Any]] = []
        for row in rival_rows:
            comp = self.db.get(CompetitorEntity, row.competitor_id)
            if comp is None:
                continue
            r_reputacion = _clamp((row.rating_avg / 5.0) * 100) if row.rating_avg else 50.0
            r_actividad = _post_recency_score(row.last_post_date)
            r_volumen = _clamp((row.review_count or 0) / max(client_reviews, 1) * 60)
            rivals_data.append({
                "label": comp.name_short or comp.maps_url[:40],
                "scores": {
                    "Reputación": round(r_reputacion, 1),
                    "Actividad": round(r_actividad, 1),
                    "Volumen": round(r_volumen, 1),
                    "Velocidad": 50.0,   # not tracked per competitor
                    "Tendencia": 50.0,   # not tracked per competitor
                },
            })

        return {
            "client": axes,
            "rivals": rivals_data,
            "scraped_at": max(
                (r.scraped_at for r in rival_rows), default=None
            ),
            "has_data": len(rival_rows) > 0,
        }
