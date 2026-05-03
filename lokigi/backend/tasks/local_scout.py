"""tasks/local_scout.py — Celery beat task that runs Local Scout every 48 h."""

from __future__ import annotations

import logging
from uuid import UUID

from app import database
from app.local_scout_service import LocalScoutOrchestrator
from celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(
    name="tasks.local_scout.run_local_scout_all_users",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def run_local_scout_all_users(self) -> dict:  # type: ignore[override]
    """Scrape all active competitor URLs for every user and persist to competitor_history."""
    db = database.SessionLocal()
    try:
        orchestrator = LocalScoutOrchestrator(db)
        result = orchestrator.run_all_users()
        logger.info(
            "LocalScout completed: users=%s scraped=%s failed=%s",
            result["users_processed"],
            result["total_scraped"],
            result["total_failed"],
        )
        return result
    except Exception as exc:
        db.rollback()
        logger.exception("LocalScout task failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery.task(
    name="tasks.local_scout.run_local_scout_for_user",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def run_local_scout_for_user(self, user_id: str) -> dict:  # type: ignore[override]
    """On-demand scrape for a single user (e.g., triggered from the Growth dashboard)."""
    db = database.SessionLocal()
    try:
        orchestrator = LocalScoutOrchestrator(db)
        result = orchestrator.run_for_user(UUID(user_id))
        return result
    except Exception as exc:
        db.rollback()
        logger.exception("LocalScout single-user task failed for user_id=%s", user_id)
        raise self.retry(exc=exc)
    finally:
        db.close()
