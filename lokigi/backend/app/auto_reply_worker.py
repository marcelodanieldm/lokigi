from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import engine
from .models import GoogleConnection, Review, StarterProfileSettings
from .services import send_review_reply, should_auto_send_now

logger = logging.getLogger(__name__)


async def run_auto_reply_dispatch() -> None:
    """Dispatch pending AUTO_REPLY suggestions based on user schedule.

    Rules:
    - Only for users with manual approval disabled.
    - `instant`: send as soon as possible.
    - `delay_1h`: wait 1 hour from reply_decided_at.
    """
    now_utc = datetime.now(timezone.utc)

    with Session(engine) as db:
        pending = db.scalars(
            select(Review)
            .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
            .where(
                Review.reply_action == "AUTO_REPLY",
                Review.reply_sent_at.is_(None),
                Review.reply_public_text.is_not(None),
                GoogleConnection.manual_approval_enabled.is_(False),
            )
            .order_by(Review.reply_decided_at.asc())
        ).all()

        for review in pending:
            connection = db.get(GoogleConnection, review.connection_id)
            if not connection:
                continue

            profile_settings = db.scalar(
                select(StarterProfileSettings).where(StarterProfileSettings.user_id == connection.user_id)
            )
            schedule = profile_settings.response_schedule if profile_settings else "instant"

            if not should_auto_send_now(
                manual_approval_enabled=connection.manual_approval_enabled,
                response_schedule=schedule,
                decided_at=review.reply_decided_at,
                now_utc=now_utc,
            ):
                continue

            try:
                await send_review_reply(db=db, review=review, reply_text=review.reply_public_text or "")
            except HTTPException:
                logger.exception("Auto-reply dispatch failed for review %s", review.review_id)
            except Exception:
                logger.exception("Unexpected auto-reply failure for review %s", review.review_id)
