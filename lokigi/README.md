# Lokigi

Lokigi is a backend service for Google Business Profile automation.

It supports OAuth2 location linking, webhook ingestion of new reviews, review integrity persistence, and automated NLP decisions for reply vs alert.

## What is implemented

- Google OAuth2 flow for Business Profile linking.
- One-location-per-user and one-user-per-location constraints.
- Pub/Sub webhook processing for `NEW_REVIEW` notifications.
- Review storage with collision protection by `review_id` and payload hash.
- Automatic review decision engine:
  - detect language
  - `stars < 3` => `ALERT`
  - `stars > 4` => `AUTO_REPLY` with business + author names
  - sensitive mid-rating content => `ALERT`
- Decision persistence in database for auditability.
- Deployment assets for Docker Compose and Caddy.

## Quick start (local)

From `backend/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1
```

This installs dependencies, runs migrations, creates a local test user, and starts the API.

## Main endpoints

- `GET /health`
- `GET /oauth/google/start?user_id=<UUID>&location_id=<LOCATION_ID>`
- `GET /oauth/google/callback`
- `POST /webhooks/google/reviews`

## Full project documentation

- `docs/README.md`
- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/DATA_MODEL.md`
- `docs/OPERATIONS.md`
- `docs/NLP_REPLY_AUTOMATION.md`

## Existing backend guides

- `backend/LOCAL_DEV.md`
- `backend/deploy/DEPLOYMENT.md`

