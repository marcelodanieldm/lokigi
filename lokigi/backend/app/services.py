from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID
from urllib.parse import urlencode

from cryptography.fernet import Fernet
from fastapi import HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import httpx
from itsdangerous import URLSafeSerializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .google_client import GoogleBusinessProfileClient, GoogleOAuthError
from .models import GoogleConnection, PendingResponse, Review, StarterProfileSettings, SubscriptionProfile, User
from .review_reply_engine import build_dynamic_review_prompt, generate_reply_by_tone, generate_review_reply_decision
from .socketio_server import emit_new_review_ready


logger = logging.getLogger(__name__)


class OAuthStateManager:
    def __init__(self, secret: str) -> None:
        self.serializer = URLSafeSerializer(secret_key=secret, salt="google-oauth-state")

    def sign(self, payload: dict[str, Any]) -> str:
        return self.serializer.dumps(payload)

    def verify(self, raw_state: str) -> dict[str, Any]:
        try:
            return self.serializer.loads(raw_state)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Invalid oauth state") from exc


class TokenCipher:
    def __init__(self, fernet_key: str) -> None:
        if not fernet_key:
            raise RuntimeError("Missing OAUTH_TOKEN_ENCRYPTION_KEY")
        self.fernet = Fernet(fernet_key.encode("utf-8"))

    def encrypt(self, value: str) -> str:
        return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        return self.fernet.decrypt(value.encode("utf-8")).decode("utf-8")


def sha256_json(data: dict[str, Any]) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_google_oauth_url(user_id: str, location_id: str | None = None, extra_state: dict[str, Any] | None = None) -> str:
    state_manager = OAuthStateManager(settings.oauth_state_secret)
    state_payload: dict[str, Any] = {"user_id": user_id}
    if location_id:
        state_payload["location_id"] = location_id
    if extra_state:
        state_payload.update(extra_state)
    state = state_manager.sign(state_payload)

    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/business.manage",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


async def upsert_google_connection(db: Session, code: str, state: str) -> GoogleConnection:
    state_payload = OAuthStateManager(settings.oauth_state_secret).verify(state)
    user_id = state_payload.get("user_id")
    location_id = state_payload.get("location_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id in state")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    client = GoogleBusinessProfileClient(
        settings.google_client_id,
        settings.google_client_secret,
        settings.google_redirect_uri,
    )

    try:
        token_data = await client.exchange_code(code)
        locations = await client.list_accessible_locations(token_data["access_token"])
    except GoogleOAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not locations:
        raise HTTPException(status_code=403, detail="No accessible locations found in your Google Business Profile")

    # If location_id is provided, use it; otherwise auto-select the first (for zero-friction flow)
    if location_id:
        selected = next((loc for loc in locations if loc["location_id"] == location_id), None)
        if not selected:
            raise HTTPException(status_code=403, detail="Selected location is not accessible by this Google account")
    else:
        selected = locations[0]

    existing_for_user = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user.id))
    if existing_for_user and existing_for_user.location_id != selected["location_id"]:
        subscription_profile = db.scalar(select(SubscriptionProfile).where(SubscriptionProfile.user_id == user.id))
        current_plan = (subscription_profile.subscription_plan if subscription_profile else "starter").lower()
        if current_plan == "starter":
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "growth_upgrade_required",
                    "message": "El Plan Starter incluye una sola ubicación. Para conectar una segunda ubicación debes actualizar a Growth.",
                    "upgrade_required": True,
                    "target_plan": "growth",
                    "current_location_id": existing_for_user.location_id,
                    "requested_location_id": selected["location_id"],
                    "upsell_url": f"/starter/subscription?user_id={user.id}&upsell=growth&requested_location_id={selected['location_id']}",
                },
            )
        raise HTTPException(
            status_code=409,
            detail="User already linked to a different location. Only one location is allowed.",
        )

    existing_for_location = db.scalar(select(GoogleConnection).where(GoogleConnection.location_id == selected["location_id"]))
    if existing_for_location and existing_for_location.user_id != user.id:
        raise HTTPException(status_code=409, detail="Location already linked to another user")

    cipher = TokenCipher(settings.oauth_token_encryption_key)
    refresh_token = token_data.get("refresh_token")
    if not refresh_token and existing_for_user:
        refresh_token = cipher.decrypt(existing_for_user.encrypted_refresh_token)
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Google did not return refresh token")

    if existing_for_user:
        connection = existing_for_user
    else:
        connection = GoogleConnection(user_id=user.id, location_id=selected["location_id"], google_account_name=selected["account_name"])
        db.add(connection)

    connection.google_account_name = selected["account_name"]
    connection.business_name = selected.get("title") or selected["account_name"]
    connection.location_id = selected["location_id"]
    connection.encrypted_access_token = cipher.encrypt(token_data["access_token"])
    connection.encrypted_refresh_token = cipher.encrypt(refresh_token)
    connection.token_expiry = token_data["expires_at"]

    db.commit()
    db.refresh(connection)
    return connection


def verify_pubsub_jwt(authorization_header: str) -> None:
    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization_header.split(" ", 1)[1]
    req = google_requests.Request()
    try:
        id_info = id_token.verify_oauth2_token(token, req, settings.google_pubsub_audience)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid webhook token") from exc

    issuer = id_info.get("iss")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=401, detail="Invalid webhook issuer")


def parse_pubsub_push(body: dict[str, Any]) -> dict[str, Any]:
    message = body.get("message", {})
    data = message.get("data")
    if not data:
        raise HTTPException(status_code=400, detail="Missing pubsub message data")

    try:
        decoded = base64.b64decode(data).decode("utf-8")
        return json.loads(decoded)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid pubsub payload") from exc


def parse_google_review_event_body(body: dict[str, Any]) -> dict[str, Any]:
    if "message" in body:
        return parse_pubsub_push(body)
    return body


def extract_location_id(payload: dict[str, Any]) -> str:
    for key in ("locationName", "location", "location_name"):
        value = payload.get(key)
        if isinstance(value, str) and "/locations/" in value:
            return value.split("/")[-1]
        if isinstance(value, str) and value.isdigit():
            return value
    review_name = payload.get("reviewName") or payload.get("review_name") or payload.get("name")
    if isinstance(review_name, str) and "/locations/" in review_name:
        parts = review_name.split("/")
        if "locations" in parts:
            index = parts.index("locations")
            if index + 1 < len(parts):
                return parts[index + 1]
    raise HTTPException(status_code=400, detail="Cannot determine location_id from webhook payload")


def extract_review_name(payload: dict[str, Any]) -> str:
    for key in ("reviewName", "review_name", "name"):
        value = payload.get(key)
        if isinstance(value, str) and "reviews/" in value:
            return value
    raise HTTPException(status_code=400, detail="Cannot determine reviewName from payload")


def extract_review_id(payload: dict[str, Any]) -> str:
    direct = payload.get("reviewId") or payload.get("review_id")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    review_name = payload.get("reviewName") or payload.get("review_name") or payload.get("name")
    if isinstance(review_name, str) and review_name.strip():
        return review_name.rstrip("/").split("/")[-1]

    raise HTTPException(status_code=400, detail="Cannot determine review_id from payload")


def build_review_processing_task_payload(body: dict[str, Any]) -> dict[str, Any]:
    payload = parse_google_review_event_body(body)
    rating_value = payload.get("starRating", payload.get("rating"))
    try:
        rating = int(rating_value) if rating_value is not None else None
    except (TypeError, ValueError):
        rating = None

    comment = payload.get("comment")
    if comment is not None and not isinstance(comment, str):
        comment = str(comment)

    return {
        "review_id": extract_review_id(payload),
        "rating": rating,
        "comment": comment,
        "location_id": extract_location_id(payload),
        "review_name": payload.get("reviewName") or payload.get("review_name") or payload.get("name"),
        "notification_type": payload.get("notificationType") or payload.get("notification_type"),
        "reviewer": payload.get("reviewer") if isinstance(payload.get("reviewer"), dict) else {},
        "payload": payload,
    }


async def ensure_valid_access_token(db: Session, connection: GoogleConnection) -> str:
    cipher = TokenCipher(settings.oauth_token_encryption_key)
    access_token = cipher.decrypt(connection.encrypted_access_token)

    if connection.token_expiry > datetime.now(timezone.utc):
        return access_token

    refresh_token = cipher.decrypt(connection.encrypted_refresh_token)
    client = GoogleBusinessProfileClient(
        settings.google_client_id,
        settings.google_client_secret,
        settings.google_redirect_uri,
    )

    try:
        refresh_data = await client.refresh_access_token(refresh_token)
    except GoogleOAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    connection.encrypted_access_token = cipher.encrypt(refresh_data["access_token"])
    connection.token_expiry = refresh_data["expires_at"]
    db.commit()
    db.refresh(connection)

    return refresh_data["access_token"]


def parse_google_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def apply_review_reply_decision(review: Review, decision: dict[str, Any]) -> None:
    alert = decision.get("internal_alert", {})
    review.reply_action = decision.get("action")
    review.reply_detected_language = decision.get("detected_language")
    review.reply_reason = decision.get("reason")
    review.reply_public_text = decision.get("public_reply")
    review.reply_alert_priority = alert.get("priority")
    review.reply_alert_category = alert.get("category")
    review.reply_alert_summary = alert.get("summary")
    review.reply_alert_next_step = alert.get("recommended_next_step")
    review.reply_decided_at = datetime.now(timezone.utc)


def upsert_pending_response(
    db: Session,
    *,
    review: Review,
    draft_text: str,
    prompt_text: str | None,
    tone: str | None,
    model_name: str | None,
    status: str = "pending",
) -> PendingResponse:
    pending = db.scalar(select(PendingResponse).where(PendingResponse.review_pk == review.id))
    if pending is None:
        pending = PendingResponse(
            review_pk=review.id,
            draft_text=draft_text,
            status=status,
            tone=tone,
            prompt_text=prompt_text,
            model_name=model_name,
        )
        db.add(pending)
    else:
        pending.draft_text = draft_text
        pending.status = status
        pending.tone = tone
        pending.prompt_text = prompt_text
        pending.model_name = model_name
    db.commit()
    db.refresh(pending)
    return pending


def apply_forbidden_words_filter(text: str | None, forbidden_words_raw: str | None) -> str | None:
    if not text:
        return text
    if not forbidden_words_raw:
        return text

    tokens = [
        chunk.strip().lower()
        for chunk in re.split(r"[\n,;]+", forbidden_words_raw)
        if chunk.strip()
    ]
    if not tokens:
        return text

    filtered = text
    for token in tokens:
        pattern = re.compile(re.escape(token), re.IGNORECASE)
        filtered = pattern.sub("***", filtered)
    return filtered


def should_auto_send_now(
    *,
    manual_approval_enabled: bool,
    response_schedule: str,
    decided_at: datetime | None,
    now_utc: datetime | None = None,
) -> bool:
    """Return True when an AUTO_REPLY can be published immediately.

    - manual approval ON  => never auto-send
    - schedule instant    => send now
    - schedule delay_1h   => send only after 1 hour from decided_at
    """
    if manual_approval_enabled:
        return False

    schedule = (response_schedule or "instant").strip().lower()
    if schedule == "instant":
        return True

    if schedule == "delay_1h":
        if decided_at is None:
            return False
        if decided_at.tzinfo is None:
            decided_at = decided_at.replace(tzinfo=timezone.utc)
        now = now_utc or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return now >= decided_at + timedelta(hours=1)

    return True


def emit_review_alert(review: Review) -> None:
    logger.warning(
        "REVIEW_ALERT location_id=%s review_id=%s priority=%s category=%s summary=%s",
        review.location_id,
        review.review_id,
        review.reply_alert_priority,
        review.reply_alert_category,
        review.reply_alert_summary,
    )


def _resolve_brand_tone(raw_tone: str | None) -> str:
    """Normalize UI tone aliases to engine-supported values."""
    tone = (raw_tone or "cercano").strip().lower()
    if tone in {"amistoso", "friendly"}:
        return "cercano"
    if tone in {"formal", "moderno", "cercano"}:
        return tone
    return "cercano"


def _apply_brand_tone_reply(
    *,
    connection: GoogleConnection,
    review_comment: str,
    review_rating: int | None,
    author_name: str,
    decision: dict[str, Any],
) -> dict[str, Any]:
    """Inject brand-tone reply text when decision is AUTO_REPLY."""
    if decision.get("action") != "AUTO_REPLY":
        return decision

    decision["public_reply"] = generate_reply_by_tone(
        tone=_resolve_brand_tone(connection.preferred_tone),
        review_text=review_comment,
        stars=review_rating,
        business_name=connection.business_name or connection.google_account_name,
        author_name=author_name,
    )
    return decision


async def send_negative_review_alert_notification(review: Review, connection: GoogleConnection) -> None:
    """Push immediate negative-review notification to webhook when configured."""
    endpoint = settings.negative_review_alert_webhook_url.strip()
    if not endpoint:
        return

    headers = {"Content-Type": "application/json"}
    token = settings.negative_review_alert_webhook_token.strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "event": "starter.negative_review_alert",
        "review_id": review.review_id,
        "location_id": review.location_id,
        "business_name": connection.business_name or connection.google_account_name,
        "author": review.author_display_name,
        "rating": review.rating,
        "summary": review.reply_alert_summary,
        "priority": review.reply_alert_priority,
        "created_at": review.created_at.isoformat() if review.created_at else None,
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            if response.status_code >= 400:
                logger.warning(
                    "Negative alert webhook failed status=%s review_id=%s",
                    response.status_code,
                    review.review_id,
                )
    except Exception:
        logger.exception("Negative alert webhook request failed for review_id=%s", review.review_id)


async def store_new_review_from_webhook(db: Session, webhook_payload: dict[str, Any]) -> Review:
    notification_type = webhook_payload.get("notificationType") or webhook_payload.get("notification_type")
    if notification_type and notification_type.upper() != "NEW_REVIEW":
        raise HTTPException(status_code=202, detail="Notification ignored")

    location_id = extract_location_id(webhook_payload)
    review_name = extract_review_name(webhook_payload)

    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.location_id == location_id))
    if not connection:
        raise HTTPException(status_code=404, detail="Location not linked")

    access_token = await ensure_valid_access_token(db, connection)
    client = GoogleBusinessProfileClient(
        settings.google_client_id,
        settings.google_client_secret,
        settings.google_redirect_uri,
    )

    try:
        review_data = await client.get_review(access_token, review_name)
    except GoogleOAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    review_id = review_data.get("reviewId") or review_data.get("name")
    if not review_id:
        raise HTTPException(status_code=400, detail="reviewId not found in Google review payload")

    payload_hash = sha256_json(review_data)
    existing = db.scalar(select(Review).where(Review.review_id == review_id))
    if existing:
        if existing.raw_payload_hash != payload_hash:
            raise HTTPException(status_code=409, detail="reviewId collision with different payload")
        return existing

    reviewer = review_data.get("reviewer", {})
    author_metadata = {
        "reviewer_name": reviewer.get("displayName"),
        "profile_photo_url": reviewer.get("profilePhotoUrl"),
        "is_anonymous": bool(reviewer.get("isAnonymous")),
    }

    review = Review(
        connection_id=connection.id,
        review_id=review_id,
        location_id=location_id,
        rating=review_data.get("starRating"),
        comment=review_data.get("comment"),
        create_time=parse_google_time(review_data.get("createTime")),
        update_time=parse_google_time(review_data.get("updateTime")),
        author_display_name=reviewer.get("displayName"),
        author_profile_photo_url=reviewer.get("profilePhotoUrl"),
        author_is_anonymous=bool(reviewer.get("isAnonymous")),
        author_metadata=author_metadata,
        author_metadata_hash=sha256_json(author_metadata),
        raw_payload=review_data,
        raw_payload_hash=payload_hash,
    )

    db.add(review)
    db.commit()
    db.refresh(review)
    return review


async def store_review_from_event_payload(db: Session, event_payload: dict[str, Any]) -> Review:
    payload = event_payload.get("payload") if isinstance(event_payload.get("payload"), dict) else event_payload
    notification_type = payload.get("notificationType") or payload.get("notification_type")
    if notification_type and str(notification_type).upper() != "NEW_REVIEW":
        raise HTTPException(status_code=202, detail="Notification ignored")

    rating = event_payload.get("rating")
    comment = event_payload.get("comment")
    if rating is None and not comment and event_payload.get("review_name"):
        return await store_new_review_from_webhook(db=db, webhook_payload=payload)

    location_id = event_payload.get("location_id") or extract_location_id(payload)
    review_id = event_payload.get("review_id") or extract_review_id(payload)

    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.location_id == location_id))
    if not connection:
        raise HTTPException(status_code=404, detail="Location not linked")

    reviewer = event_payload.get("reviewer") if isinstance(event_payload.get("reviewer"), dict) else {}
    author_metadata = {
        "reviewer_name": reviewer.get("displayName"),
        "profile_photo_url": reviewer.get("profilePhotoUrl"),
        "is_anonymous": bool(reviewer.get("isAnonymous")),
    }
    payload_hash = sha256_json(payload)
    existing = db.scalar(select(Review).where(Review.review_id == review_id))
    if existing:
        existing.rating = rating
        existing.comment = comment
        existing.author_display_name = reviewer.get("displayName") or existing.author_display_name
        existing.author_profile_photo_url = reviewer.get("profilePhotoUrl") or existing.author_profile_photo_url
        existing.author_is_anonymous = bool(reviewer.get("isAnonymous"))
        existing.author_metadata = author_metadata
        existing.author_metadata_hash = sha256_json(author_metadata)
        existing.raw_payload = payload
        existing.raw_payload_hash = payload_hash
        db.commit()
        db.refresh(existing)
        return existing

    review = Review(
        connection_id=connection.id,
        review_id=review_id,
        location_id=location_id,
        rating=rating,
        comment=comment,
        create_time=parse_google_time(payload.get("createTime")),
        update_time=parse_google_time(payload.get("updateTime")),
        author_display_name=reviewer.get("displayName"),
        author_profile_photo_url=reviewer.get("profilePhotoUrl"),
        author_is_anonymous=bool(reviewer.get("isAnonymous")),
        author_metadata=author_metadata,
        author_metadata_hash=sha256_json(author_metadata),
        raw_payload=payload,
        raw_payload_hash=payload_hash,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


async def process_review_workflow(db: Session, review_id: UUID | str) -> Review:
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    connection = db.get(GoogleConnection, review.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found for review")

    if review.reply_action and review.reply_decided_at is not None:
        return review

    profile_settings = db.scalar(
        select(StarterProfileSettings).where(StarterProfileSettings.user_id == connection.user_id)
    )

    decision = generate_review_reply_decision(
        review_text=review.comment or "",
        stars=review.rating,
        business_name=connection.business_name or connection.google_account_name,
        author_name=review.author_display_name or "there",
    )
    decision = _apply_brand_tone_reply(
        connection=connection,
        review_comment=review.comment or "",
        review_rating=review.rating,
        author_name=review.author_display_name or "there",
        decision=decision,
    )
    decision["public_reply"] = apply_forbidden_words_filter(
        decision.get("public_reply"),
        profile_settings.forbidden_words if profile_settings else "",
    )

    apply_review_reply_decision(review, decision)
    db.commit()
    db.refresh(review)

    if review.reply_action == "AUTO_REPLY" and review.reply_public_text:
        prompt_text = build_dynamic_review_prompt(
            tone=_resolve_brand_tone(connection.preferred_tone),
            review_text=review.comment or "",
            business_name=connection.business_name or connection.google_account_name,
            author_name=review.author_display_name or "",
        )
        upsert_pending_response(
            db,
            review=review,
            draft_text=review.reply_public_text,
            prompt_text=prompt_text,
            tone=_resolve_brand_tone(connection.preferred_tone),
            model_name=settings.review_reply_llm_model if settings.review_reply_llm_enabled else "local-template-fallback",
        )
        await emit_new_review_ready(
            user_id=str(connection.user_id),
            review_pk=str(review.id),
            author=review.author_display_name or "Cliente",
            comment=review.comment or "",
        )

    if review.reply_action == "ALERT":
        emit_review_alert(review)
        await send_negative_review_alert_notification(review, connection)
    elif (
        review.reply_action == "AUTO_REPLY"
        and review.reply_sent_at is None
        and review.reply_public_text
        and (review.rating or 0) >= 4
        and should_auto_send_now(
            manual_approval_enabled=connection.manual_approval_enabled,
            response_schedule=profile_settings.response_schedule if profile_settings else "instant",
            decided_at=review.reply_decided_at,
        )
    ):
        try:
            await send_review_reply(db=db, review=review, reply_text=review.reply_public_text)
        except HTTPException:
            logger.exception("Immediate auto-send failed for review %s", review.review_id)

    return review


# ── Review Approval helpers ───────────────────────────────────────────────────

def get_pending_approvals(db: Session, user_id: str) -> list[Review]:
    """Return reviews with an AUTO_REPLY suggestion not yet sent, for a user."""
    return list(
        db.scalars(
            select(Review)
            .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
            .where(
                GoogleConnection.user_id == user_id,
                Review.reply_action == "AUTO_REPLY",
                Review.reply_sent_at.is_(None),
                Review.reply_public_text.is_not(None),
            )
            .order_by(Review.created_at.desc())
        ).all()
    )


async def send_review_reply(db: Session, review: Review, reply_text: str) -> Review:
    """Post an approved reply to Google and persist the result.

    Raises HTTPException:
      - 409 when Google returns a duplicate-reply error
      - 502 on any other Google API failure
      - 404 when the parent connection is missing
    """
    connection = db.get(GoogleConnection, review.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found for review")

    access_token = await ensure_valid_access_token(db, connection)
    client = GoogleBusinessProfileClient(
        settings.google_client_id,
        settings.google_client_secret,
        settings.google_redirect_uri,
    )

    # review_name format expected by GBP: accounts/{acct}/locations/{loc}/reviews/{id}
    review_name = (
        f"{connection.google_account_name}/locations/{review.location_id}/reviews/{review.review_id}"
    )

    try:
        await client.post_reply(access_token, review_name, reply_text)
    except GoogleOAuthError as exc:
        if "duplicate_reply" in str(exc):
            raise HTTPException(
                status_code=409,
                detail="Esta reseña ya tiene una respuesta publicada en Google.",
            ) from exc
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    review.reply_approved_text = reply_text
    review.reply_sent_at = datetime.now(timezone.utc)
    pending = db.scalar(select(PendingResponse).where(PendingResponse.review_pk == review.id))
    if pending:
        pending.status = "sent"
        pending.approved_text = reply_text
        pending.draft_text = reply_text
    db.commit()
    db.refresh(review)
    return review


async def list_locations_for_user(db: Session, user_id: str) -> dict[str, Any]:
    """List available Google Business Profile locations for a user.

    Returns:
        - status='not-found': User does not exist
        - status='need-oauth': User exists but has no connection. Includes oauth_url to initiate flow
        - status='connected': User has a connection. Includes the linked location details
    """
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    user = db.get(User, user_uuid)
    if not user:
        return {"status": "not-found", "message": "User not found"}

    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_uuid))
    if not connection:
        # User exists but has no connection. Provide OAuth URL to start the flow.
        oauth_url = build_google_oauth_url(
            user_id=str(user_uuid),
            location_id="",  # No location selected yet
            extra_state={"starter_flow": True, "location_selection": True},
        )
        return {
            "status": "need-oauth",
            "message": "Connect your Google Business Profile to link locations",
            "oauth_url": oauth_url,
        }

    # User has a connection. Return the linked location.
    return {
        "status": "connected",
        "locations": [
            {
                "location_id": connection.location_id,
                "title": connection.business_name or connection.google_account_name,
                "account_name": connection.google_account_name,
            }
        ],
    }


async def regenerate_review_reply(db: Session, review: Review) -> Review:
    """Re-run the NLP engine and overwrite the suggested reply (does not send)."""
    connection = db.get(GoogleConnection, review.connection_id)
    business_name = (
        connection.business_name or connection.google_account_name if connection else "our business"
    )
    decision = generate_review_reply_decision(
        review_text=review.comment or "",
        stars=review.rating,
        business_name=business_name,
        author_name=review.author_display_name or "there",
    )
    if connection:
        decision = _apply_brand_tone_reply(
            connection=connection,
            review_comment=review.comment or "",
            review_rating=review.rating,
            author_name=review.author_display_name or "there",
            decision=decision,
        )
    if connection:
        profile_settings = db.scalar(
            select(StarterProfileSettings).where(StarterProfileSettings.user_id == connection.user_id)
        )
        decision["public_reply"] = apply_forbidden_words_filter(
            decision.get("public_reply"),
            profile_settings.forbidden_words if profile_settings else "",
        )
    apply_review_reply_decision(review, decision)
    # Reset sent state so the new suggestion goes back to pending
    review.reply_sent_at = None
    review.reply_approved_text = None
    db.commit()
    db.refresh(review)
    if review.reply_public_text:
        tone = _resolve_brand_tone(connection.preferred_tone if connection else "cercano")
        prompt_text = build_dynamic_review_prompt(
            tone=tone,
            review_text=review.comment or "",
            business_name=business_name,
            author_name=review.author_display_name or "",
        )
        upsert_pending_response(
            db,
            review=review,
            draft_text=review.reply_public_text,
            prompt_text=prompt_text,
            tone=tone,
            model_name=settings.review_reply_llm_model if settings.review_reply_llm_enabled else "local-template-fallback",
        )
    return review
