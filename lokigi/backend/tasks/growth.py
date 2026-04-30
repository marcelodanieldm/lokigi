from __future__ import annotations

import logging
from uuid import UUID

from app import database
from app.growth_scraper_service import GrowthScraperService
from celery_app import celery


logger = logging.getLogger(__name__)


@celery.task(name="tasks.growth.run_initial_radar_sync")
def run_initial_radar_sync(user_id: str, client_google_place_id: str | None = None) -> dict[str, int | str]:
    db = database.SessionLocal()
    try:
        service = GrowthScraperService(db)
        result = service.scrape_and_persist_all_competitors(
            user_id=UUID(user_id),
            include_benchmark=True,
            client_google_place_id=client_google_place_id,
        )
        return {
            "status": "completed",
            "processed": int(result.get("processed") or 0),
            "success": int(result.get("success") or 0),
            "failed": int(result.get("failed") or 0),
        }
    except Exception:
        db.rollback()
        logger.exception("Initial Growth radar sync failed for user_id=%s", user_id)
        raise
    finally:
        db.close()