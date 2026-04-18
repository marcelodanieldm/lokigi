from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.growth_event_notification_service import (
    ALLOWED_CHANNELS,
    ALLOWED_EVENT_TYPES,
    ALLOWED_SEVERITIES,
    GrowthEventNotificationService,
)
from app.models import User

router = APIRouter(tags=["growth-events"])


class GrowthEventPublishRequest(BaseModel):
    user_id: UUID
    event_type: str = Field(description="guard_change|threat_detected|roi_snapshot")
    severity: str = Field(default="medium", description="low|medium|high|critical")
    title: str = Field(min_length=4, max_length=180)
    message: str = Field(min_length=8, max_length=1200)
    context_payload: dict = Field(default_factory=dict)
    report_url: str | None = None
    dedupe_key: str | None = Field(default=None, max_length=255)
    channels: list[str] | None = None


class GrowthEventResponse(BaseModel):
    id: UUID
    event_type: str
    channel: str
    severity: str
    title: str
    message: str
    status: str
    report_url: str | None
    context_payload: dict
    is_seen: bool
    created_at: datetime
    processed_at: datetime | None


def _validate_publish_security(x_webhook_secret: str) -> None:
    if settings.webhook_shared_secret and x_webhook_secret != settings.webhook_shared_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")


@router.post(
    "/internal/growth/events/publish",
    summary="Publish Growth retention/upsell event notifications",
)
def publish_growth_event(
    request: GrowthEventPublishRequest,
    x_webhook_secret: str = Header(default="", alias="X-Webhook-Secret"),
    db: Session = Depends(get_db),
):
    _validate_publish_security(x_webhook_secret)

    if request.event_type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event_type")
    if request.severity not in ALLOWED_SEVERITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid severity")
    if request.channels:
        invalid = [ch for ch in request.channels if ch not in ALLOWED_CHANNELS]
        if invalid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid channels: {invalid}")

    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthEventNotificationService(db)
    try:
        result = service.publish_event(
            user_id=request.user_id,
            event_type=request.event_type,
            severity=request.severity,
            title=request.title,
            message=request.message,
            context_payload=request.context_payload,
            report_url=request.report_url,
            dedupe_key=request.dedupe_key,
            channels=request.channels,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "ok": True,
        "dedupe_key": result.dedupe_key,
        "created": len(result.created),
        "skipped_channels": result.skipped_channels,
        "items": [
            {
                "id": item.id,
                "event_type": item.event_type,
                "channel": item.channel,
                "severity": item.severity,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in result.created
        ],
    }


@router.get(
    "/api/growth/events",
    response_model=list[GrowthEventResponse],
    summary="List Growth in-app events",
)
def list_growth_events(
    user_id: UUID,
    include_seen: bool = Query(default=False),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthEventNotificationService(db)
    rows = service.list_events(user_id=user_id, include_seen=include_seen, limit=limit)
    return [
        GrowthEventResponse(
            id=row.id,
            event_type=row.event_type,
            channel=row.channel,
            severity=row.severity,
            title=row.title,
            message=row.message,
            status=row.status,
            report_url=row.report_url,
            context_payload=row.context_payload,
            is_seen=row.is_seen,
            created_at=row.created_at,
            processed_at=row.processed_at,
        )
        for row in rows
    ]


@router.post(
    "/api/growth/events/{event_id}/seen",
    summary="Mark one Growth in-app event as seen",
)
def mark_growth_event_seen(
    event_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthEventNotificationService(db)
    try:
        row = service.mark_seen(user_id=user_id, event_id=event_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {"ok": True, "event_id": row.id, "is_seen": row.is_seen, "seen_at": row.seen_at}
