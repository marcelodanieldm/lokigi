from __future__ import annotations

import base64
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from cryptography.fernet import Fernet
from fastapi import HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from itsdangerous import URLSafeSerializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .google_client import GoogleBusinessProfileClient, GoogleOAuthError
from .models import GoogleConnection, Review, User
from .review_reply_engine import generate_review_reply_decision


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


def build_google_oauth_url(user_id: str, location_id: str) -> str:
    state_manager = OAuthStateManager(settings.oauth_state_secret)
    state = state_manager.sign({"user_id": user_id, "location_id": location_id})

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

    if not user_id or not location_id:
        raise HTTPException(status_code=400, detail="Missing user_id or location_id in state")

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

    selected = next((loc for loc in locations if loc["location_id"] == location_id), None)
    if not selected:
        raise HTTPException(status_code=403, detail="Selected location is not accessible by this Google account")

    existing_for_user = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user.id))
    if existing_for_user and existing_for_user.location_id != location_id:
        raise HTTPException(
            status_code=409,
            detail="User already linked to a different location. Only one location is allowed.",
        )

    existing_for_location = db.scalar(select(GoogleConnection).where(GoogleConnection.location_id == location_id))
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
        connection = GoogleConnection(user_id=user.id, location_id=location_id, google_account_name=selected["account_name"])
        db.add(connection)

    connection.google_account_name = selected["account_name"]
    connection.business_name = selected.get("title") or selected["account_name"]
    connection.location_id = location_id
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


def extract_location_id(payload: dict[str, Any]) -> str:
    for key in ("locationName", "location", "location_name"):
        value = payload.get(key)
        if isinstance(value, str) and "/locations/" in value:
            return value.split("/")[-1]
        if isinstance(value, str) and value.isdigit():
            return value
    raise HTTPException(status_code=400, detail="Cannot determine location_id from webhook payload")


def extract_review_name(payload: dict[str, Any]) -> str:
    for key in ("reviewName", "review_name", "name"):
        value = payload.get(key)
        if isinstance(value, str) and "reviews/" in value:
            return value
    raise HTTPException(status_code=400, detail="Cannot determine reviewName from payload")


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


def emit_review_alert(review: Review) -> None:
    logger.warning(
        "REVIEW_ALERT location_id=%s review_id=%s priority=%s category=%s summary=%s",
        review.location_id,
        review.review_id,
        review.reply_alert_priority,
        review.reply_alert_category,
        review.reply_alert_summary,
    )
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


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

        if not existing.reply_action:
            decision = generate_review_reply_decision(
                review_text=existing.comment or "",
                stars=existing.rating,
                business_name=connection.business_name or connection.google_account_name,
                author_name=existing.author_display_name or "there",
            )
            apply_review_reply_decision(existing, decision)
            if existing.reply_action == "ALERT":
                emit_review_alert(existing)
            db.commit()
            db.refresh(existing)
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

    decision = generate_review_reply_decision(
        review_text=review.comment or "",
        stars=review.rating,
        business_name=connection.business_name or connection.google_account_name,
        author_name=review.author_display_name or "there",
    )
    apply_review_reply_decision(review, decision)

    db.add(review)
    db.commit()
    db.refresh(review)

    if review.reply_action == "ALERT":
        emit_review_alert(review)

    return review
