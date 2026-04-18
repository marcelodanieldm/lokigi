import base64
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import select

from app.models import GoogleConnection, Review


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
    assert "Conectar Google Maps" in onboarding.text

    connect = client.get(f"/starter/connect-google?user_id={test_user.id}&location_id=222", follow_redirects=False)
    assert connect.status_code in (302, 307)
    oauth_url = connect.headers["location"]

    state = parse_qs(urlparse(oauth_url).query)["state"][0]
    callback = client.get(
        f"/oauth/google/callback?code=oauth-code-starter&state={state}",
        follow_redirects=False,
    )
    assert callback.status_code in (302, 307)
    assert callback.headers["location"] == f"/starter/dashboard?user_id={test_user.id}"

    dashboard = client.get(callback.headers["location"])
    assert dashboard.status_code == 200
    assert "Starter Dashboard" in dashboard.text
    assert "Conectado" in dashboard.text
    assert "My Store" in dashboard.text

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
    assert first.json()["status"] == "stored"
    assert first.json()["decision_action"] == "AUTO_REPLY"
    assert first.json()["detected_language"].startswith("es")
    assert "public_reply" in first.json()

    second = client.post("/webhooks/google/reviews", json=body, headers={"Authorization": "Bearer test"})
    assert second.status_code == 200
    assert second.json()["status"] == "stored"

    reviews = db_session.scalars(select(Review).where(Review.location_id == "222")).all()
    assert len(reviews) == 1
    assert reviews[0].review_id == "review-abc-1"
    assert reviews[0].author_display_name == "John D"


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
