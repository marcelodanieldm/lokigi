# Architecture

## Scope

Lokigi provides a backend for Google Business Profile integration with OAuth2 and review ingestion.

## Main components

- FastAPI app: `backend/app/main.py`
- Business logic services: `backend/app/services.py`
- Google API client: `backend/app/google_client.py`
- NLP decision engine: `backend/app/review_reply_engine.py`
- Persistence layer: SQLAlchemy models in `backend/app/models.py`
- Migrations: Alembic in `backend/alembic/`

## Core flow: OAuth link

1. Client calls `GET /oauth/google/start` with `user_id` and `location_id`.
2. Backend creates signed `state` and redirects to Google OAuth consent.
3. Google returns to `GET /oauth/google/callback`.
4. Backend exchanges auth code, verifies location access, and stores encrypted tokens.
5. Enforced constraints:
   - one location per user
   - one user per location

## Core flow: New review webhook

1. Pub/Sub push hits `POST /webhooks/google/reviews`.
2. Backend verifies JWT bearer token and optional shared secret.
3. Payload is decoded from Pub/Sub message data.
4. Backend fetches review detail from Google Business Profile API.
5. Review is stored with uniqueness and hash integrity checks.
6. NLP decision engine computes `AUTO_REPLY` or `ALERT` and persists decision fields.
7. For `ALERT`, backend emits internal alert log event.

## Security controls

- OAuth state signing.
- Encrypted access/refresh tokens at rest.
- Pub/Sub OIDC JWT verification.
- Optional `X-Webhook-Secret` header validation.
- Trusted host middleware.

## Resilience and idempotency

- Duplicate webhook events resolve by unique `review_id`.
- Payload hash collision protection rejects conflicting duplicated IDs.
- Access token refresh is automatic when expired.
