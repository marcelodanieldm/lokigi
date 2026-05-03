from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx


class GoogleOAuthError(RuntimeError):
    pass


class GoogleBusinessProfileClient:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    async def exchange_code(self, code: str) -> dict[str, Any]:
        payload = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post("https://oauth2.googleapis.com/token", data=payload)
        if response.status_code >= 400:
            raise GoogleOAuthError(f"Google token exchange failed: {response.text}")
        data = response.json()
        expires_in = int(data.get("expires_in", 3600))
        data["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return data

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        payload = {
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post("https://oauth2.googleapis.com/token", data=payload)
        if response.status_code >= 400:
            raise GoogleOAuthError(f"Google token refresh failed: {response.text}")
        data = response.json()
        expires_in = int(data.get("expires_in", 3600))
        data["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return data

    async def list_accessible_locations(self, access_token: str) -> list[dict[str, str]]:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            accounts_resp = await client.get(
                "https://mybusinessaccountmanagement.googleapis.com/v1/accounts", headers=headers
            )
            if accounts_resp.status_code >= 400:
                raise GoogleOAuthError(f"Cannot list Google accounts: {accounts_resp.text}")

            locations: list[dict[str, str]] = []
            for account in accounts_resp.json().get("accounts", []):
                account_name = account["name"]
                loc_resp = await client.get(
                    f"https://mybusinessbusinessinformation.googleapis.com/v1/{account_name}/locations",
                    headers=headers,
                    params={"pageSize": 100, "readMask": "name,title,storeCode"},
                )
                if loc_resp.status_code >= 400:
                    continue

                for item in loc_resp.json().get("locations", []):
                    location_name = item.get("name", "")
                    location_id = location_name.split("/")[-1] if location_name else ""
                    if location_id:
                        locations.append(
                            {
                                "account_name": account_name,
                                "location_name": location_name,
                                "location_id": location_id,
                                "title": item.get("title", ""),
                            }
                        )
        return locations

    async def get_review(self, access_token: str, review_name: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"https://mybusiness.googleapis.com/v4/{review_name}", headers=headers)
        if response.status_code >= 400:
            raise GoogleOAuthError(f"Cannot fetch review detail: {response.text}")
        return response.json()

    async def get_location_metadata(
        self,
        access_token: str,
        location_name: str,
        read_mask: str | None = None,
    ) -> dict[str, Any]:
        """Fetch GBP location profile metadata for read-only UI sections.

        Includes title, storefrontAddress, regularHours.weekdayDescriptions and profile.description.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "readMask": read_mask or "title,storefrontAddress,regularHours.weekdayDescriptions,profile.description",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"https://mybusinessbusinessinformation.googleapis.com/v1/{location_name}",
                headers=headers,
                params=params,
            )
        if response.status_code >= 400:
            raise GoogleOAuthError(f"Cannot fetch location metadata: {response.text}")
        return response.json()

    async def update_location_description(
        self,
        access_token: str,
        location_name: str,
        description: str,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        params = {"updateMask": "profile.description"}
        payload = {"profile": {"description": description}}

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.patch(
                f"https://mybusinessbusinessinformation.googleapis.com/v1/{location_name}",
                headers=headers,
                params=params,
                json=payload,
            )
        if response.status_code >= 400:
            raise GoogleOAuthError(f"Cannot update location profile description: {response.text}")
        return response.json()

    async def post_reply(self, access_token: str, review_name: str, comment: str) -> dict[str, Any]:
        """Post or overwrite the owner reply for a review.

        Google API: PUT https://mybusiness.googleapis.com/v4/{name}/reply
        Returns the reply resource on success.
        Raises GoogleOAuthError with a ``duplicate`` hint when status is 409.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
                f"https://mybusiness.googleapis.com/v4/{review_name}/reply",
                headers=headers,
                json={"comment": comment},
            )
        if response.status_code == 409:
            raise GoogleOAuthError("duplicate_reply")
        if response.status_code >= 400:
            raise GoogleOAuthError(f"Cannot post reply: {response.text}")
        return response.json()

    async def create_local_post(
        self,
        access_token: str,
        account_name: str,
        location_id: str,
        summary: str,
        topic_type: str = "STANDARD",
        language_code: str = "es",
    ) -> dict[str, Any]:
        """Create a Google Business Profile Local Post.

        Google API: POST https://mybusiness.googleapis.com/v4/{parent}/localPosts
        where parent = accounts/{accountId}/locations/{locationId}
        Returns the created localPost resource.
        """
        parent = f"{account_name}/locations/{location_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "languageCode": language_code,
            "summary": summary,
            "topicType": topic_type,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"https://mybusiness.googleapis.com/v4/{parent}/localPosts",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            raise GoogleOAuthError(f"Cannot create local post: {response.text}")
        return response.json()

    # ── Google Q&A API ────────────────────────────────────────────────────────

    async def list_questions(
        self,
        access_token: str,
        location_name: str,
        page_size: int = 10,
        answers_per_question: int = 1,
    ) -> list[dict[str, Any]]:
        """List Q&A questions for a location (unanswered first).

        Google API: GET https://mybusiness.googleapis.com/v4/{parent}/questions
        Returns a flat list of question resource dicts.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        params: dict[str, Any] = {
            "pageSize": page_size,
            "answersPerQuestion": answers_per_question,
            "orderBy": "update_time desc",
        }
        questions: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            next_page_token: str | None = None
            while True:
                if next_page_token:
                    params["pageToken"] = next_page_token
                response = await client.get(
                    f"https://mybusiness.googleapis.com/v4/{location_name}/questions",
                    headers=headers,
                    params=params,
                )
                if response.status_code == 404:
                    # Q&A not enabled for this location
                    return []
                if response.status_code >= 400:
                    raise GoogleOAuthError(f"Cannot list Q&A questions: {response.text}")
                data = response.json()
                questions.extend(data.get("questions", []))
                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break
        return questions

    async def post_qa_answer(
        self,
        access_token: str,
        question_name: str,
        answer_text: str,
    ) -> dict[str, Any]:
        """Create or overwrite the owner answer for a Q&A question.

        Google API: POST https://mybusiness.googleapis.com/v4/{parent}/answers:upsert
        Returns the answer resource on success.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"https://mybusiness.googleapis.com/v4/{question_name}/answers:upsert",
                headers=headers,
                json={"answer": {"text": answer_text}},
            )
        if response.status_code >= 400:
            raise GoogleOAuthError(f"Cannot post Q&A answer: {response.text}")
        return response.json()

