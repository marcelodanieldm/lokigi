from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import GrowthEventNotification, User

logger = logging.getLogger(__name__)


ALLOWED_EVENT_TYPES = {"guard_change", "threat_detected", "roi_snapshot"}
ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}
ALLOWED_CHANNELS = {"push", "email", "in_app"}


@dataclass
class PublishResult:
    created: list[GrowthEventNotification]
    skipped_channels: list[str]
    dedupe_key: str


class GrowthEventNotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def publish_event(
        self,
        *,
        user_id: UUID,
        event_type: str,
        severity: str,
        title: str,
        message: str,
        context_payload: dict[str, Any] | None = None,
        report_url: str | None = None,
        dedupe_key: str | None = None,
        channels: list[str] | None = None,
    ) -> PublishResult:
        if event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError("Unsupported event_type")
        if severity not in ALLOWED_SEVERITIES:
            raise ValueError("Unsupported severity")

        context_payload = context_payload or {}
        selected_channels = channels if channels else self._default_channels_for_event(event_type)
        selected_channels = [c for c in selected_channels if c in ALLOWED_CHANNELS]
        if not selected_channels:
            raise ValueError("No valid channel provided")

        resolved_key = dedupe_key or self._build_dedupe_key(
            user_id=user_id,
            event_type=event_type,
            context_payload=context_payload,
        )

        if self._is_duplicate(resolved_key):
            return PublishResult(created=[], skipped_channels=selected_channels, dedupe_key=resolved_key)

        now = datetime.now(timezone.utc)
        created: list[GrowthEventNotification] = []
        skipped: list[str] = []

        for channel in selected_channels:
            if channel == "push" and severity in {"high", "critical"} and self._push_cooldown_reached(user_id):
                skipped.append(channel)
                continue

            row = GrowthEventNotification(
                user_id=user_id,
                event_type=event_type,
                channel=channel,
                severity=severity,
                title=title,
                message=message,
                context_payload=context_payload,
                report_url=report_url,
                dedupe_key=resolved_key,
                status="pending",
                send_attempts=0,
                is_seen=(channel != "in_app"),
                created_at=now,
            )
            self.db.add(row)
            created.append(row)

        self.db.commit()
        for row in created:
            self.db.refresh(row)
        return PublishResult(created=created, skipped_channels=skipped, dedupe_key=resolved_key)

    async def dispatch_pending(self, *, batch_size: int = 50) -> dict[str, int]:
        rows = self.db.scalars(
            select(GrowthEventNotification)
            .where(GrowthEventNotification.status == "pending")
            .order_by(GrowthEventNotification.created_at.asc())
            .limit(batch_size)
        ).all()

        sent = 0
        failed = 0
        for row in rows:
            try:
                await self._dispatch_row(row)
                row.status = "sent"
                row.processed_at = datetime.now(timezone.utc)
                row.send_attempts += 1
                row.last_error = None
                self.db.add(row)
                sent += 1
            except Exception as exc:
                row.status = "failed"
                row.processed_at = datetime.now(timezone.utc)
                row.send_attempts += 1
                row.last_error = str(exc)[:500]
                self.db.add(row)
                failed += 1
                logger.exception("Growth event dispatch failed for %s", row.id)

        self.db.commit()
        return {"processed": len(rows), "sent": sent, "failed": failed}

    def list_events(self, *, user_id: UUID, include_seen: bool = False, limit: int = 50) -> list[GrowthEventNotification]:
        stmt = (
            select(GrowthEventNotification)
            .where(GrowthEventNotification.user_id == user_id)
            .order_by(desc(GrowthEventNotification.created_at))
            .limit(limit)
        )
        if not include_seen:
            stmt = stmt.where(
                and_(
                    GrowthEventNotification.channel == "in_app",
                    GrowthEventNotification.is_seen.is_(False),
                )
            )
        return list(self.db.scalars(stmt).all())

    def mark_seen(self, *, user_id: UUID, event_id: UUID) -> GrowthEventNotification:
        row = self.db.get(GrowthEventNotification, event_id)
        if not row or row.user_id != user_id:
            raise ValueError("Event not found")
        row.is_seen = True
        row.seen_at = datetime.now(timezone.utc)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _default_channels_for_event(self, event_type: str) -> list[str]:
        if event_type == "guard_change":
            return ["push", "in_app"]
        if event_type == "threat_detected":
            return ["push", "email", "in_app"]
        return ["email", "in_app"]

    def _build_dedupe_key(self, *, user_id: UUID, event_type: str, context_payload: dict[str, Any]) -> str:
        scope = (
            context_payload.get("keyword")
            or context_payload.get("competitor_name")
            or context_payload.get("zone")
            or "global"
        )
        day = datetime.now(timezone.utc).date().isoformat()
        return f"{user_id}:{event_type}:{scope}:{day}"

    def _is_duplicate(self, dedupe_key: str) -> bool:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        existing = self.db.scalars(
            select(GrowthEventNotification.id).where(
                GrowthEventNotification.dedupe_key == dedupe_key,
                GrowthEventNotification.created_at >= since,
            )
        ).first()
        return existing is not None

    def _push_cooldown_reached(self, user_id: UUID) -> bool:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        count = self.db.scalars(
            select(GrowthEventNotification.id).where(
                GrowthEventNotification.user_id == user_id,
                GrowthEventNotification.channel == "push",
                GrowthEventNotification.severity.in_(["high", "critical"]),
                GrowthEventNotification.created_at >= since,
            )
        ).all()
        return len(count) >= 2

    async def _dispatch_row(self, row: GrowthEventNotification) -> None:
        if row.channel in {"push", "in_app"}:
            logger.info(
                "Growth event dispatched (%s): user=%s event=%s severity=%s",
                row.channel,
                row.user_id,
                row.event_type,
                row.severity,
            )
            return

        if row.channel == "email":
            await self._dispatch_email(row)
            return

        raise RuntimeError(f"Unsupported channel: {row.channel}")

    async def _dispatch_email(self, row: GrowthEventNotification) -> None:
        user = self.db.get(User, row.user_id)
        if not user or not user.email:
            raise RuntimeError("User email not available")

        if not settings.sendgrid_api_key:
            logger.info("SendGrid disabled; skipping external email send for event %s", row.id)
            return

        html_body = (
            f"<p>{row.message}</p>"
            + (f"<p><a href=\"{row.report_url}\">Ver reporte</a></p>" if row.report_url else "")
        )
        payload = {
            "personalizations": [{"to": [{"email": user.email}]}],
            "from": {"email": settings.sendgrid_from_email},
            "subject": row.title,
            "content": [
                {"type": "text/plain", "value": row.message},
                {"type": "text/html", "value": html_body},
            ],
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
            )
        if response.status_code >= 400:
            raise RuntimeError(f"SendGrid request failed: {response.status_code} {response.text[:250]}")
