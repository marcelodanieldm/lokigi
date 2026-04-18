from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from threading import Lock
from typing import Any
from urllib.parse import urlparse
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    GoogleConnection,
    GrowthBenchmarkComparison,
    GrowthClientKeywordMetric,
    GrowthClientServiceSnapshot,
    GrowthClientSnapshot,
    GrowthCompetitor,
    GrowthCompetitorKeywordMetric,
    GrowthCompetitorServiceSnapshot,
    GrowthCompetitorSnapshot,
)

logger = logging.getLogger(__name__)


@dataclass
class ScrapedPlaceData:
    rating_avg: float | None
    review_count_total: int | None
    posts_count_7d: int | None
    posts_count_30d: int | None
    services: list[str]
    keyword_counts: dict[str, int]
    raw_source: str


class ProxyRotator:
    """Round-robin proxy selector driven by comma-separated env list."""

    def __init__(self, proxies: list[str]) -> None:
        self._proxies = [item.strip() for item in proxies if item and item.strip()]
        self._index = 0
        self._lock = Lock()

    def next(self) -> str | None:
        if not self._proxies:
            return None
        with self._lock:
            selected = self._proxies[self._index]
            self._index = (self._index + 1) % len(self._proxies)
            return selected


class GrowthScraperService:
    """Python Playwright-based scraper for Growth competitor intelligence."""

    _token_pattern = re.compile(r"[a-zA-Z0-9\-]{3,}")
    _rating_pattern = re.compile(r"([0-5][\.,][0-9])")
    _review_count_pattern = re.compile(r"([0-9][0-9\.,\s]*)\s*(reviews|reseñas)", re.IGNORECASE)

    def __init__(self, db: Session) -> None:
        self.db = db
        proxies = settings.growth_proxy_pool.split(",") if settings.growth_proxy_pool else []
        self._proxy_rotator = ProxyRotator(proxies)

    def scrape_and_persist_competitor(
        self,
        *,
        user_id: UUID,
        competitor_id: UUID,
        include_benchmark: bool = True,
        client_google_place_id: str | None = None,
    ) -> dict[str, Any]:
        competitor = self.db.get(GrowthCompetitor, competitor_id)
        if not competitor or competitor.user_id != user_id:
            raise ValueError("Competitor not found for user")

        observed_at = datetime.now(timezone.utc).replace(microsecond=0)
        extraction_job_id = uuid4()

        competitor_data = asyncio.run(
            self._scrape_place(competitor.google_place_id)
        )
        self._upsert_competitor_snapshot(
            competitor_id=competitor.id,
            observed_at=observed_at,
            extraction_job_id=extraction_job_id,
            data=competitor_data,
        )

        client_data: ScrapedPlaceData | None = None
        if include_benchmark:
            resolved_client_place_id = (
                client_google_place_id.strip()
                if client_google_place_id and client_google_place_id.strip()
                else self._resolve_client_google_place_id(user_id)
            )
            if resolved_client_place_id:
                client_data = asyncio.run(self._scrape_place(resolved_client_place_id))
                self._upsert_client_snapshot(
                    user_id=user_id,
                    observed_at=observed_at,
                    extraction_job_id=extraction_job_id,
                    data=client_data,
                )
                self._upsert_benchmark(
                    user_id=user_id,
                    competitor_id=competitor.id,
                    observed_at=observed_at,
                    client=client_data,
                    competitor=competitor_data,
                )

        self.db.commit()
        return {
            "competitor_id": str(competitor.id),
            "competitor_name": competitor.name,
            "observed_at": observed_at.isoformat(),
            "proxy_pool_size": len(self._proxy_rotator._proxies),
            "competitor_snapshot": {
                "rating_avg": competitor_data.rating_avg,
                "review_count_total": competitor_data.review_count_total,
                "posts_count_7d": competitor_data.posts_count_7d,
                "posts_count_30d": competitor_data.posts_count_30d,
                "services_count": len(competitor_data.services),
                "top_keywords": self._keyword_payload(competitor_data.keyword_counts),
            },
            "client_snapshot_available": client_data is not None,
        }

    def scrape_and_persist_all_competitors(
        self,
        *,
        user_id: UUID,
        include_benchmark: bool = True,
        client_google_place_id: str | None = None,
    ) -> dict[str, Any]:
        competitors = self.db.scalars(
            select(GrowthCompetitor).where(
                GrowthCompetitor.user_id == user_id,
                GrowthCompetitor.is_active.is_(True),
            )
        ).all()

        if not competitors:
            return {"processed": 0, "results": []}

        results: list[dict[str, Any]] = []
        for competitor in competitors:
            try:
                item = self.scrape_and_persist_competitor(
                    user_id=user_id,
                    competitor_id=competitor.id,
                    include_benchmark=include_benchmark,
                    client_google_place_id=client_google_place_id,
                )
                results.append({"ok": True, **item})
            except Exception as exc:  # pragma: no cover - defensive telemetry path
                logger.exception("Growth scrape failed for competitor %s", competitor.id)
                self.db.rollback()
                results.append(
                    {
                        "ok": False,
                        "competitor_id": str(competitor.id),
                        "competitor_name": competitor.name,
                        "error": str(exc),
                    }
                )

        return {
            "processed": len(competitors),
            "success": sum(1 for item in results if item.get("ok")),
            "failed": sum(1 for item in results if not item.get("ok")),
            "results": results,
        }

    async def _scrape_place(self, google_place_id: str) -> ScrapedPlaceData:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:  # pragma: no cover - environment guard
            raise RuntimeError(
                "Playwright is not installed. Run 'pip install -r backend/requirements.txt' "
                "and 'playwright install chromium'."
            ) from exc

        proxy_url = self._proxy_rotator.next()
        playwright_proxy = self._build_playwright_proxy(proxy_url)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.growth_playwright_headless,
                proxy=playwright_proxy,
            )
            try:
                context = await browser.new_context(
                    user_agent=settings.growth_playwright_user_agent,
                    locale="es-ES",
                    timezone_id="UTC",
                )
                page = await context.new_page()
                url = f"https://www.google.com/maps/place/?q=place_id:{google_place_id}"

                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=settings.growth_playwright_timeout_ms,
                )
                await page.wait_for_timeout(2000)

                extracted = await page.evaluate(
                    """
                    () => {
                      const bodyText = document.body ? document.body.innerText : '';
                      const title = document.title || '';
                      const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                      const ldJson = scripts
                        .map((item) => item.textContent || '')
                        .filter(Boolean);
                      const serviceButtons = Array.from(document.querySelectorAll('button, span, div'))
                        .map((el) => (el.textContent || '').trim())
                        .filter((txt) => txt.length > 2 && txt.length < 80)
                        .slice(0, 800);
                      return { bodyText, title, ldJson, serviceButtons };
                    }
                    """
                )
            finally:
                await browser.close()

        return self._parse_scraped_payload(extracted)

    def _parse_scraped_payload(self, payload: dict[str, Any]) -> ScrapedPlaceData:
        body_text = str(payload.get("bodyText") or "")
        title = str(payload.get("title") or "")
        ld_json_items = payload.get("ldJson") or []
        service_candidates = payload.get("serviceButtons") or []

        rating = self._extract_rating(body_text, title, ld_json_items)
        review_count = self._extract_review_count(body_text, ld_json_items)
        posts_7d, posts_30d = self._extract_post_counts(body_text)
        services = self._extract_services(service_candidates, ld_json_items)
        keyword_counts = self._extract_keywords(body_text, services)

        return ScrapedPlaceData(
            rating_avg=rating,
            review_count_total=review_count,
            posts_count_7d=posts_7d,
            posts_count_30d=posts_30d,
            services=services,
            keyword_counts=keyword_counts,
            raw_source="google_maps_public_playwright",
        )

    def _extract_rating(self, body_text: str, title: str, ld_json_items: list[str]) -> float | None:
        for blob in [title, body_text]:
            hit = self._rating_pattern.search(blob)
            if hit:
                try:
                    value = float(hit.group(1).replace(",", "."))
                    if 0 <= value <= 5:
                        return round(value, 2)
                except ValueError:
                    continue

        for item in ld_json_items:
            try:
                parsed = json.loads(item)
            except json.JSONDecodeError:
                continue
            for candidate in self._walk_json(parsed):
                if isinstance(candidate, dict) and "ratingValue" in candidate:
                    try:
                        value = float(str(candidate["ratingValue"]).replace(",", "."))
                        if 0 <= value <= 5:
                            return round(value, 2)
                    except (TypeError, ValueError):
                        continue
        return None

    def _extract_review_count(self, body_text: str, ld_json_items: list[str]) -> int | None:
        hit = self._review_count_pattern.search(body_text)
        if hit:
            return self._parse_int(hit.group(1))

        for item in ld_json_items:
            try:
                parsed = json.loads(item)
            except json.JSONDecodeError:
                continue
            for candidate in self._walk_json(parsed):
                if isinstance(candidate, dict) and "reviewCount" in candidate:
                    return self._parse_int(str(candidate["reviewCount"]))
        return None

    def _extract_post_counts(self, body_text: str) -> tuple[int | None, int | None]:
        # Best-effort extraction from localized page text.
        week_patterns = [r"(\d+)\s+publicaciones?\s+en\s+los\s+[úu]ltimos\s+7\s+d[ií]as", r"(\d+)\s+posts?\s+in\s+the\s+last\s+7\s+days"]
        month_patterns = [r"(\d+)\s+publicaciones?\s+en\s+los\s+[úu]ltimos\s+30\s+d[ií]as", r"(\d+)\s+posts?\s+in\s+the\s+last\s+30\s+days"]

        posts_7d = self._first_int_match(body_text, week_patterns)
        posts_30d = self._first_int_match(body_text, month_patterns)
        return posts_7d, posts_30d

    def _extract_services(self, candidates: list[str], ld_json_items: list[str]) -> list[str]:
        services: set[str] = set()

        blacklist = {
            "google maps",
            "share",
            "save",
            "website",
            "call",
            "directions",
            "overview",
            "reviews",
            "reseñas",
            "photos",
            "más",
            "menu",
        }

        for item in candidates:
            normalized = self._normalize_service(item)
            if not normalized:
                continue
            lowered = normalized.lower()
            if lowered in blacklist:
                continue
            if len(lowered) < 3 or len(lowered) > 70:
                continue
            services.add(normalized)

        for item in ld_json_items:
            try:
                parsed = json.loads(item)
            except json.JSONDecodeError:
                continue
            for candidate in self._walk_json(parsed):
                if isinstance(candidate, dict):
                    for key in ["servesCuisine", "keywords", "description"]:
                        value = candidate.get(key)
                        if isinstance(value, str):
                            for token in value.split(","):
                                normalized = self._normalize_service(token)
                                if normalized and 2 < len(normalized) < 70:
                                    services.add(normalized)
                        if isinstance(value, list):
                            for token in value:
                                normalized = self._normalize_service(str(token))
                                if normalized and 2 < len(normalized) < 70:
                                    services.add(normalized)

        return sorted(services)[:60]

    def _extract_keywords(self, body_text: str, services: list[str]) -> dict[str, int]:
        stopwords = {
            "para",
            "con",
            "por",
            "una",
            "unos",
            "unas",
            "sobre",
            "desde",
            "hasta",
            "this",
            "that",
            "from",
            "the",
            "and",
            "google",
            "maps",
            "reseñas",
            "reviews",
        }
        counts: dict[str, int] = {}

        for service in services:
            for token in self._token_pattern.findall(service.lower()):
                if token in stopwords or len(token) < 3:
                    continue
                counts[token] = counts.get(token, 0) + 2

        text_sample = body_text.lower()[:30000]
        for token in self._token_pattern.findall(text_sample):
            if token in stopwords or len(token) < 3:
                continue
            counts[token] = counts.get(token, 0) + 1

        # Keep strongest keywords only.
        items = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)[:25]
        return {k: v for k, v in items}

    def _upsert_competitor_snapshot(
        self,
        *,
        competitor_id: UUID,
        observed_at: datetime,
        extraction_job_id: UUID,
        data: ScrapedPlaceData,
    ) -> None:
        snapshot = self.db.scalars(
            select(GrowthCompetitorSnapshot).where(
                GrowthCompetitorSnapshot.competitor_id == competitor_id,
                GrowthCompetitorSnapshot.observed_at == observed_at,
            )
        ).first()
        if snapshot is None:
            snapshot = GrowthCompetitorSnapshot(
                competitor_id=competitor_id,
                observed_at=observed_at,
            )

        snapshot.review_count_total = data.review_count_total
        snapshot.rating_avg = data.rating_avg
        snapshot.posts_count_7d = data.posts_count_7d
        snapshot.posts_count_30d = data.posts_count_30d
        snapshot.services_count = len(data.services)
        snapshot.data_source = data.raw_source
        snapshot.extraction_job_id = extraction_job_id
        self.db.add(snapshot)
        self.db.flush()

        self.db.query(GrowthCompetitorServiceSnapshot).filter_by(
            competitor_id=competitor_id,
            observed_at=observed_at,
        ).delete(synchronize_session=False)
        for service in data.services:
            self.db.add(
                GrowthCompetitorServiceSnapshot(
                    competitor_id=competitor_id,
                    observed_at=observed_at,
                    service_name_normalized=service.lower(),
                    service_name_raw=service,
                )
            )

        period_start, period_end = self._period_30d(observed_at)
        self.db.query(GrowthCompetitorKeywordMetric).filter_by(
            competitor_id=competitor_id,
            period_start=period_start,
            period_end=period_end,
        ).delete(synchronize_session=False)
        for keyword, mentions in self._keyword_payload(data.keyword_counts):
            self.db.add(
                GrowthCompetitorKeywordMetric(
                    competitor_id=competitor_id,
                    period_start=period_start,
                    period_end=period_end,
                    keyword=keyword,
                    mentions_count=mentions,
                )
            )

    def _upsert_client_snapshot(
        self,
        *,
        user_id: UUID,
        observed_at: datetime,
        extraction_job_id: UUID,
        data: ScrapedPlaceData,
    ) -> None:
        snapshot = self.db.scalars(
            select(GrowthClientSnapshot).where(
                GrowthClientSnapshot.user_id == user_id,
                GrowthClientSnapshot.observed_at == observed_at,
            )
        ).first()
        if snapshot is None:
            snapshot = GrowthClientSnapshot(user_id=user_id, observed_at=observed_at)

        snapshot.review_count_total = data.review_count_total
        snapshot.rating_avg = data.rating_avg
        snapshot.posts_count_7d = data.posts_count_7d
        snapshot.posts_count_30d = data.posts_count_30d
        snapshot.services_count = len(data.services)
        snapshot.data_source = data.raw_source
        snapshot.extraction_job_id = extraction_job_id
        self.db.add(snapshot)
        self.db.flush()

        self.db.query(GrowthClientServiceSnapshot).filter_by(
            user_id=user_id,
            observed_at=observed_at,
        ).delete(synchronize_session=False)
        for service in data.services:
            self.db.add(
                GrowthClientServiceSnapshot(
                    user_id=user_id,
                    observed_at=observed_at,
                    service_name_normalized=service.lower(),
                    service_name_raw=service,
                )
            )

        period_start, period_end = self._period_30d(observed_at)
        self.db.query(GrowthClientKeywordMetric).filter_by(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
        ).delete(synchronize_session=False)
        for keyword, mentions in self._keyword_payload(data.keyword_counts):
            self.db.add(
                GrowthClientKeywordMetric(
                    user_id=user_id,
                    period_start=period_start,
                    period_end=period_end,
                    keyword=keyword,
                    mentions_count=mentions,
                )
            )

    def _upsert_benchmark(
        self,
        *,
        user_id: UUID,
        competitor_id: UUID,
        observed_at: datetime,
        client: ScrapedPlaceData,
        competitor: ScrapedPlaceData,
    ) -> None:
        row = self.db.scalars(
            select(GrowthBenchmarkComparison).where(
                GrowthBenchmarkComparison.user_id == user_id,
                GrowthBenchmarkComparison.competitor_id == competitor_id,
                GrowthBenchmarkComparison.observed_at == observed_at,
            )
        ).first()
        if row is None:
            row = GrowthBenchmarkComparison(
                user_id=user_id,
                competitor_id=competitor_id,
                observed_at=observed_at,
            )

        row.rating_gap = self._safe_gap(client.rating_avg, competitor.rating_avg)
        row.review_count_gap = self._safe_gap_int(client.review_count_total, competitor.review_count_total)
        row.review_growth_30d_gap = self._safe_gap_int(client.review_count_total, competitor.review_count_total)
        row.posting_freq_30d_gap = self._safe_gap_int(client.posts_count_30d, competitor.posts_count_30d)

        client_total = sum(client.keyword_counts.values())
        competitor_total = sum(competitor.keyword_counts.values())
        if client_total and competitor_total:
            row.keyword_share_gap = round(((client_total - competitor_total) / max(competitor_total, 1)) * 100, 2)
        else:
            row.keyword_share_gap = None

        self.db.add(row)

    def _resolve_client_google_place_id(self, user_id: UUID) -> str | None:
        # This is a pragmatic fallback: some accounts store place_id as location_id.
        conn = self.db.scalars(select(GoogleConnection).where(GoogleConnection.user_id == user_id)).first()
        if not conn:
            return None
        location_id = (conn.location_id or "").strip()
        if location_id.startswith("ChI"):
            return location_id
        return None

    def _build_playwright_proxy(self, proxy_url: str | None) -> dict[str, str] | None:
        if not proxy_url:
            return None
        parsed = urlparse(proxy_url)
        if not parsed.scheme or not parsed.hostname:
            return None

        server = f"{parsed.scheme}://{parsed.hostname}"
        if parsed.port:
            server = f"{server}:{parsed.port}"

        proxy: dict[str, str] = {"server": server}
        if parsed.username:
            proxy["username"] = parsed.username
        if parsed.password:
            proxy["password"] = parsed.password
        return proxy

    def _period_30d(self, observed_at: datetime) -> tuple[date, date]:
        period_end = observed_at.date()
        period_start = period_end - timedelta(days=29)
        return period_start, period_end

    def _keyword_payload(self, keyword_counts: dict[str, int]) -> list[tuple[str, int]]:
        return sorted(keyword_counts.items(), key=lambda pair: pair[1], reverse=True)[:20]

    def _parse_int(self, value: str) -> int | None:
        digits = re.sub(r"[^0-9]", "", value)
        if not digits:
            return None
        try:
            return int(digits)
        except ValueError:
            return None

    def _first_int_match(self, text: str, patterns: list[str]) -> int | None:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None

    def _normalize_service(self, value: str) -> str | None:
        cleaned = re.sub(r"\s+", " ", value).strip(" .,:;\n\t")
        if not cleaned:
            return None
        return cleaned[:180]

    def _walk_json(self, node: Any) -> list[Any]:
        output: list[Any] = [node]
        if isinstance(node, dict):
            for value in node.values():
                output.extend(self._walk_json(value))
        elif isinstance(node, list):
            for value in node:
                output.extend(self._walk_json(value))
        return output

    def _safe_gap(self, left: float | None, right: float | None) -> float | None:
        if left is None or right is None:
            return None
        return round(left - right, 2)

    def _safe_gap_int(self, left: int | None, right: int | None) -> int | None:
        if left is None or right is None:
            return None
        return int(left - right)
