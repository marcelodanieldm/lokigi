# API Reference

## Health

### GET /health

Returns service liveness.

Response:

```json
{
  "status": "ok"
}
```

## OAuth

### GET /oauth/google/start

Query parameters:
- `user_id` (UUID)
- `location_id` (string)

Behavior:
- Validates OAuth settings.
- Returns redirect response to Google OAuth.

### GET /oauth/google/callback

Query parameters:
- `code`
- `state`

Behavior:
- Exchanges code for tokens.
- Validates location authorization.
- Stores or updates Google connection.

Response:

```json
{
  "status": "linked",
  "user_id": "...",
  "location_id": "..."
}
```

## Webhook

### POST /webhooks/google/reviews

Headers:
- `Authorization: Bearer <oidc-token>`
- `X-Webhook-Secret: <secret>` (required only if configured)

Body:
- Pub/Sub push message schema with base64 encoded data.

Behavior:
- Verifies auth headers.
- Parses webhook payload.
- Fetches full review from Google.
- Stores review and computes automated decision.

Success response example (`AUTO_REPLY`):

```json
{
  "status": "stored",
  "review_id": "review-123",
  "location_id": "123456789",
  "decision_action": "AUTO_REPLY",
  "detected_language": "es",
  "public_reply": "Muchas gracias..."
}
```

Success response example (`ALERT`):

```json
{
  "status": "stored",
  "review_id": "review-123",
  "location_id": "123456789",
  "decision_action": "ALERT",
  "detected_language": "en",
  "alert_priority": "HIGH",
  "alert_summary": "Low rating detected..."
}
```

Ignored notification response:

```json
{
  "status": "ignored"
}
```
