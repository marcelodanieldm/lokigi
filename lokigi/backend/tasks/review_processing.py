from __future__ import annotations

import asyncio
import logging
from typing import Any

from app import database
from app.services import process_review_workflow, store_review_from_event_payload
from celery_app import celery


logger = logging.getLogger(__name__)


@celery.task(name="tasks.review_processing.process_reviews")
def process_reviews(review_event: dict[str, Any]) -> dict[str, str | None]:
    db = database.SessionLocal()
    try:
        review = asyncio.run(store_review_from_event_payload(db=db, event_payload=review_event))
        review = asyncio.run(process_review_workflow(db=db, review_id=review.id))
        return {
            "status": "processed",
            "review_id": review.review_id,
            "location_id": review.location_id,
            "decision_action": review.reply_action,
            "alert_priority": review.reply_alert_priority,
        }
    except Exception:
        db.rollback()
        logger.exception("Queued review processing failed for review_id=%s", review_event.get("review_id"))
        raise
    finally:
        db.close()


@celery.task(name="tasks.review_processing.process_google_review")
def process_google_review(review_id: str) -> dict[str, str | None]:
    db = database.SessionLocal()
    try:
        review = asyncio.run(process_review_workflow(db=db, review_id=review_id))
        return {
            "status": "processed",
            "review_id": review.review_id,
            "location_id": review.location_id,
            "decision_action": review.reply_action,
            "alert_priority": review.reply_alert_priority,
        }
    except Exception:
        db.rollback()
        logger.exception("Queued review processing failed for review_id=%s", review_id)
        raise
    finally:
        db.close()