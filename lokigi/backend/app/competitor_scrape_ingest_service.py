from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CompetitorEntity,
    CompetitorServiceMap,
    CompetitorSnapshot,
    ScrapeRun,
    ServiceCatalog,
)

_ALLOWED_STATUS = {"ok", "partial", "error", "blocked"}
_PRICE_MAP = {
    "": "unknown",
    "$": "budget",
    "$$": "mid",
    "$$$": "premium",
    "$$$$": "luxury",
}


def _sha1(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    base = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", base.lower()).strip("-")
    return cleaned[:40] or "unknown"


def _rating_x100(value: float | None) -> int | None:
    if value is None:
        return None
    bounded = max(0.0, min(5.0, float(value)))
    return int(round(bounded * 100))


def _stable_smallint(value: str) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return int(digest[:4], 16)


def _price_bucket(raw: str | None) -> str:
    if not raw:
        return "unknown"
    token = raw.strip()
    return _PRICE_MAP.get(token, "unknown")


class CompetitorScrapeIngestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def start_run(self, *, user_id: UUID, total_targets: int) -> ScrapeRun:
        run = ScrapeRun(
            user_id=user_id,
            run_date=date.today(),
            status="running",
            total_targets=max(0, total_targets),
            total_processed=0,
            total_success=0,
            total_failed=0,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def ingest_competitor_snapshot(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        competitor_url: str,
        name: str | None,
        zone_label: str | None,
        rating_avg: float | None,
        review_count_total: int | None,
        price_level_raw: str | None,
        category: str | None,
        address_short: str | None,
        posts_30d: int | None,
        services: list[str],
        source_status: str,
    ) -> CompetitorSnapshot:
        run = self.db.get(ScrapeRun, run_id)
        if not run or run.user_id != user_id:
            raise ValueError("Run not found for user")

        status = source_status if source_status in _ALLOWED_STATUS else "error"
        url_hash = _sha1(competitor_url.strip())
        zone_code = _stable_smallint(zone_label.strip().lower()) if zone_label else 0

        competitor = self.db.scalars(
            select(CompetitorEntity).where(
                CompetitorEntity.user_id == user_id,
                CompetitorEntity.url_hash == url_hash,
            )
        ).first()
        if competitor is None:
            competitor = CompetitorEntity(
                user_id=user_id,
                url_hash=url_hash,
                maps_url=competitor_url,
                name_short=(name or "")[:120] or None,
                zone_code=zone_code,
                status="active",
            )
            self.db.add(competitor)
            self.db.flush()
        else:
            competitor.maps_url = competitor_url
            competitor.name_short = (name or competitor.name_short or "")[:120] or None
            competitor.zone_code = zone_code

        snapshot = self.db.scalars(
            select(CompetitorSnapshot).where(
                CompetitorSnapshot.scrape_run_id == run_id,
                CompetitorSnapshot.competitor_id == competitor.id,
            )
        ).first()
        if snapshot is None:
            snapshot = CompetitorSnapshot(
                scrape_run_id=run_id,
                competitor_id=competitor.id,
                observed_on=run.run_date,
            )
            self.db.add(snapshot)
            self.db.flush()

        snapshot.rating_x100 = _rating_x100(rating_avg)
        snapshot.total_reviews = max(0, int(review_count_total)) if review_count_total is not None else None
        snapshot.price_bucket = _price_bucket(price_level_raw)
        snapshot.category_code = _stable_smallint(category.strip().lower()) if category else None
        snapshot.address_hash = _sha1(address_short.strip().lower()) if address_short else None
        snapshot.posts_30d = max(0, int(posts_30d)) if posts_30d is not None else None
        snapshot.source_status = status

        self._replace_snapshot_services(snapshot_id=snapshot.id, services=services)

        run.total_processed += 1
        if status in {"ok", "partial"}:
            run.total_success += 1
        else:
            run.total_failed += 1

        if run.total_processed >= run.total_targets > 0:
            run.finished_at = datetime.now(timezone.utc)
            run.status = self._resolve_run_status(run.total_success, run.total_failed)

        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def finish_run(self, *, run_id: UUID, user_id: UUID, forced_status: str | None = None) -> ScrapeRun:
        run = self.db.get(ScrapeRun, run_id)
        if not run or run.user_id != user_id:
            raise ValueError("Run not found for user")

        run.finished_at = datetime.now(timezone.utc)
        if forced_status in _ALLOWED_STATUS:
            run.status = forced_status
        else:
            run.status = self._resolve_run_status(run.total_success, run.total_failed)

        self.db.commit()
        self.db.refresh(run)
        return run

    def _replace_snapshot_services(self, *, snapshot_id: UUID, services: list[str]) -> None:
        current = self.db.scalars(
            select(CompetitorServiceMap).where(CompetitorServiceMap.snapshot_id == snapshot_id)
        ).all()
        for row in current:
            self.db.delete(row)

        unique_services: list[str] = []
        seen: set[str] = set()
        for service in services:
            cleaned = service.strip()
            if not cleaned:
                continue
            code = _slug(cleaned)
            if code in seen:
                continue
            seen.add(code)
            unique_services.append(cleaned[:80])

        for service_name in unique_services[:40]:
            code = _slug(service_name)
            catalog = self.db.scalars(select(ServiceCatalog).where(ServiceCatalog.code == code)).first()
            if catalog is None:
                catalog = ServiceCatalog(code=code, label_short=service_name)
                self.db.add(catalog)
                self.db.flush()
            mapping = CompetitorServiceMap(snapshot_id=snapshot_id, service_id=catalog.id, present=True)
            self.db.add(mapping)

    @staticmethod
    def _resolve_run_status(success: int, failed: int) -> str:
        if failed == 0 and success > 0:
            return "ok"
        if success > 0 and failed > 0:
            return "partial"
        if failed > 0 and success == 0:
            return "error"
        return "running"
