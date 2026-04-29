import base64
import asyncio
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.models import GoogleConnection, PendingResponse, Review
from app.services import process_review_workflow
from tasks.review_processing import process_reviews


@pytest.mark.asyncio
async def test_callback_oauth_links_single_location(client, test_user, db_session, monkeypatch):
    async def fake_exchange_code(self, code):
        assert code == "oauth-code-1"
        return {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    async def fake_list_locations(self, access_token):
        assert access_token == "access-token"
        return [
            {
                "account_name": "accounts/111",
                "location_name": "accounts/111/locations/222",
                "location_id": "222",
                "title": "My Store",
            }
        ]

    monkeypatch.setattr("app.google_client.GoogleBusinessProfileClient.exchange_code", fake_exchange_code)
    monkeypatch.setattr("app.google_client.GoogleBusinessProfileClient.list_accessible_locations", fake_list_locations)

    start_response = client.get(f"/oauth/google/start?user_id={test_user.id}&location_id=222", follow_redirects=False)
    assert start_response.status_code in (302, 307)

    redirect_target = start_response.headers["location"]
    state = parse_qs(urlparse(redirect_target).query)["state"][0]

    callback_response = client.get(f"/oauth/google/callback?code=oauth-code-1&state={state}")
    assert callback_response.status_code == 200
    assert callback_response.json()["status"] == "linked"
    assert callback_response.json()["location_id"] == "222"

    connection = db_session.scalar(select(GoogleConnection).where(GoogleConnection.user_id == test_user.id))
    assert connection is not None
    assert connection.location_id == "222"


@pytest.mark.asyncio
async def test_starter_onboarding_flow_redirects_to_dashboard(client, test_user, db_session, monkeypatch):
    async def fake_exchange_code(self, code):
        assert code == "oauth-code-starter"
        return {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    async def fake_list_locations(self, access_token):
        assert access_token == "access-token"
        return [
            {
                "account_name": "accounts/111",
                "location_name": "accounts/111/locations/222",
                "location_id": "222",
                "title": "My Store",
            }
        ]

    monkeypatch.setattr("app.google_client.GoogleBusinessProfileClient.exchange_code", fake_exchange_code)
    monkeypatch.setattr("app.google_client.GoogleBusinessProfileClient.list_accessible_locations", fake_list_locations)

    onboarding = client.get(f"/starter/onboarding?user_id={test_user.id}&location_id=222")
    assert onboarding.status_code == 200
    assert "Entrar con Google y continuar" in onboarding.text

    connect = client.get(f"/starter/connect-google?user_id={test_user.id}&location_id=222", follow_redirects=False)
    assert connect.status_code in (302, 307)
    oauth_url = connect.headers["location"]

    state = parse_qs(urlparse(oauth_url).query)["state"][0]
    callback = client.get(
        f"/oauth/google/callback?code=oauth-code-starter&state={state}",
        follow_redirects=False,
    )
    assert callback.status_code in (302, 307)
    assert callback.headers["location"] == f"/starter/loading?user_id={test_user.id}"

    loading = client.get(callback.headers["location"])
    assert loading.status_code == 200
    assert "Escaneando tu perfil" in loading.text

    tone_selector = client.get(f"/starter/tone-selector?user_id={test_user.id}")
    assert tone_selector.status_code == 200
    assert "Activar mi cuenta Starter" in tone_selector.text
    assert "My Store" in tone_selector.text

    connection = db_session.scalar(select(GoogleConnection).where(GoogleConnection.user_id == test_user.id))
    assert connection is not None
    assert connection.location_id == "222"


@pytest.mark.asyncio
async def test_webhook_new_review_is_stored_idempotently(client, test_user, db_session, monkeypatch):
    async def fake_exchange_code(self, code):
        return {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    async def fake_list_locations(self, access_token):
        return [
            {
                "account_name": "accounts/111",
                "location_name": "accounts/111/locations/222",
                "location_id": "222",
                "title": "My Store",
            }
        ]

    async def fake_get_review(self, access_token, review_name):
        return {
            "name": review_name,
            "reviewId": "review-abc-1",
            "starRating": 5,
            "comment": "Excelente atencion",
            "createTime": "2026-04-18T08:00:00Z",
            "updateTime": "2026-04-18T08:00:00Z",
            "reviewer": {
                "displayName": "John D",
                "profilePhotoUrl": "https://example.com/p.png",
                "isAnonymous": False,
            },
        }

    monkeypatch.setattr("app.google_client.GoogleBusinessProfileClient.exchange_code", fake_exchange_code)
    monkeypatch.setattr("app.google_client.GoogleBusinessProfileClient.list_accessible_locations", fake_list_locations)
    monkeypatch.setattr("app.google_client.GoogleBusinessProfileClient.get_review", fake_get_review)
    monkeypatch.setattr("app.main.verify_pubsub_jwt", lambda _: None)

    def fake_delay(review_pk: str):
        asyncio.run(process_review_workflow(db=db_session, review_id=review_pk))
        return SimpleNamespace(id=f"task-{review_pk}")

    monkeypatch.setattr("app.main.process_google_review.delay", fake_delay)

    start_response = client.get(f"/oauth/google/start?user_id={test_user.id}&location_id=222", follow_redirects=False)
    state = parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]
    callback_response = client.get(f"/oauth/google/callback?code=oauth-code-2&state={state}")
    assert callback_response.status_code == 200

    payload = {
        "notificationType": "NEW_REVIEW",
        "locationName": "accounts/111/locations/222",
        "reviewName": "accounts/111/locations/222/reviews/review-abc-1",
    }
    message_data = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    body = {"message": {"data": message_data}}

    first = client.post("/webhooks/google/reviews", json=body, headers={"Authorization": "Bearer test"})
    assert first.status_code == 200
    assert first.json()["status"] == "queued"
    assert first.json()["processing_mode"] == "celery"
    assert first.json()["task_id"].startswith("task-")

    second = client.post("/webhooks/google/reviews", json=body, headers={"Authorization": "Bearer test"})
    assert second.status_code == 200
    assert second.json()["status"] == "queued"

    reviews = db_session.scalars(select(Review).where(Review.location_id == "222")).all()
    assert len(reviews) == 1
    assert reviews[0].review_id == "review-abc-1"
    assert reviews[0].author_display_name == "John D"
    assert reviews[0].reply_action == "AUTO_REPLY"
    assert reviews[0].reply_detected_language.startswith("es")
    assert reviews[0].reply_public_text


def test_queue_only_webhook_enqueues_process_reviews(client, monkeypatch):
    captured: dict[str, object] = {}
    monkeypatch.setattr("app.main.verify_pubsub_jwt", lambda _: None)

    def fake_delay(payload: dict[str, object]):
        captured.update(payload)
        return SimpleNamespace(id="task-queued-1")

    monkeypatch.setattr("app.main.process_reviews.delay", fake_delay)

    response = client.post(
        "/webhooks/google-reviews",
        json={
            "notificationType": "NEW_REVIEW",
            "locationName": "accounts/111/locations/222",
            "reviewId": "review-inline-1",
            "starRating": 5,
            "comment": "Muy buena atención",
        },
        headers={"Authorization": "Bearer test"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["queue"] == "process_reviews"
    assert captured["review_id"] == "review-inline-1"
    assert captured["rating"] == 5
    assert captured["comment"] == "Muy buena atención"


def test_process_reviews_worker_persists_pending_response(db_session, test_user):
    connection = GoogleConnection(
        user_id=test_user.id,
        google_account_name="accounts/111",
        business_name="My Store",
        location_id="222",
        encrypted_access_token="token",
        encrypted_refresh_token="refresh",
        token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        manual_approval_enabled=True,
        preferred_tone="formal",
    )
    db_session.add(connection)
    db_session.commit()

    result = process_reviews.run(
        {
            "review_id": "review-worker-1",
            "rating": 5,
            "comment": "Excelente servicio y rapidez",
            "location_id": "222",
            "review_name": "accounts/111/locations/222/reviews/review-worker-1",
            "reviewer": {"displayName": "Marcela", "profilePhotoUrl": None, "isAnonymous": False},
            "payload": {
                "notificationType": "NEW_REVIEW",
                "locationName": "accounts/111/locations/222",
                "reviewId": "review-worker-1",
                "starRating": 5,
                "comment": "Excelente servicio y rapidez",
                "reviewer": {"displayName": "Marcela", "profilePhotoUrl": None, "isAnonymous": False},
            },
        }
    )

    assert result["status"] == "processed"
    review = db_session.scalar(select(Review).where(Review.review_id == "review-worker-1"))
    assert review is not None
    pending = db_session.scalar(select(PendingResponse).where(PendingResponse.review_pk == review.id))
    assert pending is not None
    assert pending.status == "pending"
    assert pending.draft_text
    assert pending.prompt_text


@pytest.mark.asyncio
async def test_webhook_rejects_reviewid_collision_with_different_payload(client, test_user, db_session, monkeypatch):
    async def fake_exchange_code(self, code):
        return {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    async def fake_list_locations(self, access_token):
        return [
            {
                "account_name": "accounts/111",
                "location_name": "accounts/111/locations/222",
                "location_id": "222",
                "title": "My Store",
            }
        ]

    review_variants = [
        {
            "name": "accounts/111/locations/222/reviews/review-xyz",
            "reviewId": "review-collision-1",
            "starRating": 4,
            "comment": "Primera version",
            "createTime": "2026-04-18T08:00:00Z",
            "updateTime": "2026-04-18T08:00:00Z",
            "reviewer": {"displayName": "Ana", "profilePhotoUrl": None, "isAnonymous": False},
        },
        {
            "name": "accounts/111/locations/222/reviews/review-xyz",
            "reviewId": "review-collision-1",
            "starRating": 1,
            "comment": "Version conflictiva",
            "createTime": "2026-04-18T08:00:00Z",
            "updateTime": "2026-04-18T09:00:00Z",
            "reviewer": {"displayName": "Ana", "profilePhotoUrl": None, "isAnonymous": False},
        },
    ]

    async def fake_get_review(self, access_token, review_name):
        return review_variants.pop(0)

    monkeypatch.setattr("app.google_client.GoogleBusinessProfileClient.exchange_code", fake_exchange_code)
    monkeypatch.setattr("app.google_client.GoogleBusinessProfileClient.list_accessible_locations", fake_list_locations)
    monkeypatch.setattr("app.google_client.GoogleBusinessProfileClient.get_review", fake_get_review)
    monkeypatch.setattr("app.main.verify_pubsub_jwt", lambda _: None)

    def fake_delay(review_pk: str):
        asyncio.run(process_review_workflow(db=db_session, review_id=review_pk))
        return SimpleNamespace(id=f"task-{review_pk}")

    monkeypatch.setattr("app.main.process_google_review.delay", fake_delay)

    start_response = client.get(f"/oauth/google/start?user_id={test_user.id}&location_id=222", follow_redirects=False)
    state = parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]
    client.get(f"/oauth/google/callback?code=oauth-code-3&state={state}")

    payload = {
        "notificationType": "NEW_REVIEW",
        "locationName": "accounts/111/locations/222",
        "reviewName": "accounts/111/locations/222/reviews/review-xyz",
    }
    body = {"message": {"data": base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")}}

    first = client.post("/webhooks/google/reviews", json=body, headers={"Authorization": "Bearer test"})
    assert first.status_code == 200

    second = client.post("/webhooks/google/reviews", json=body, headers={"Authorization": "Bearer test"})
    assert second.status_code == 409
    assert "collision" in second.json()["detail"]
