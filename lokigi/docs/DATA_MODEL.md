# Data Model

## Tables

### users

- `id` UUID PK
- `email` unique
- `created_at`

### google_connections

- `id` UUID PK
- `user_id` FK -> users.id (cascade delete)
- `google_account_name`
- `business_name`
- `location_id` unique
- `encrypted_access_token`
- `encrypted_refresh_token`
- `token_expiry`
- `created_at`
- `updated_at`

Business constraints:
- unique user_id (one linked location per user)
- unique location_id (one owner per location)

### reviews

- `id` UUID PK
- `connection_id` FK -> google_connections.id (cascade delete)
- `review_id` unique
- `location_id` indexed
- `rating`, `comment`, `create_time`, `update_time`
- author fields and metadata hash
- raw payload and hash
- reply decision fields:
  - `reply_action`
  - `reply_detected_language`
  - `reply_reason`
  - `reply_public_text`
  - `reply_alert_priority`
  - `reply_alert_category`
  - `reply_alert_summary`
  - `reply_alert_next_step`
  - `reply_decided_at`
- `created_at`

## Migrations

- `20260418_0001`: base schema for users, connections, reviews
- `20260418_0002`: adds business name and reply decision fields

Run migrations:

```bash
alembic -c alembic.ini upgrade head
```
