# Lokigi

Lokigi is a backend service for Google Business Profile automation — review ingestion, AI-assisted reply management, Starter onboarding UX, monthly KPI analytics and sentiment reporting.

## What is implemented

### Core platform
- Google OAuth2 flow for Business Profile linking.
- One-location-per-user and one-user-per-location constraints.
- Pub/Sub webhook processing for `NEW_REVIEW` notifications.
- Review storage with collision protection by `review_id` and payload hash.
- Symmetric encryption (Fernet) for stored OAuth tokens.

### NLP reply engine (`review_reply_engine.py`)
- Language detection (ES / EN / PT / FR) via `langdetect`.
- `stars ≤ 2` → `ALERT` (high priority).
- Sensitive content detected → `ALERT` (escalate to legal/ops).
- `stars 4-5` → `AUTO_REPLY` with personalised gratitude template.
- `stars 3` → `AUTO_REPLY` with professional improvement template.
- Decision persisted in DB for full auditability.

### Starter onboarding UX — Zero-Friction Flow
- **Location discovery API**: `GET /api/locations?user_id=` detects if user is linked and returns available locations.
- **Seamless OAuth**: Modified OAuth flow allows auto-selection of the first location (for < 3-minute onboarding).
- 3-click onboarding: `/starter/onboarding` → Google consent → auto-redirect to `/starter/dashboard`.
- OAuth `state` signed with `itsdangerous`; `starter_flow` flag ensures dashboard redirect.
- Dashboard shows connection status, business name, and last 5 reviews received.

### Human approval workflow (`/starter/approvals`)
- Bootstrap 5 page (no npm, no build step) served directly by FastAPI.
- Lists all pending `AUTO_REPLY` reviews for a user.
- Per-review card: original review, editable AI suggestion, **Aprobar y Enviar** / **Regenerar** buttons.
- Handles 409 duplicate-reply from Google gracefully; shows inline error messages.
- API: `GET /api/reviews/pending`, `POST /api/reviews/{id}/approve`, `POST /api/reviews/{id}/regenerate`.

### Monthly KPI analytics
- `StarterMonthlyMetrics` table: `total_reviews`, `avg_rating`, `response_rate_pct`, `avg_response_time_minutes` grouped by month.
- SQL upsert query in `backend/sql/starter_monthly_metrics_query.sql` — ready for a daily background job.
- Tenant-isolated: all queries scoped to `user_id` via `INNER JOIN google_connections`.

### Sentiment analysis — concept extraction (`sentiment_analysis.py`)
- Lexicon-based (bilingual ES/EN), no external ML dependency.
- Polarity derived from star rating: 4-5★ → positive, 1-2★ → negative, 3★ skipped.
- 12 concept categories tracked (atención, rapidez, precio, limpieza, ambiente, etc.).
- Returns top-N positive + top-N negative concepts with counts and percentages.
- Includes `chart_data` key with aligned `labels / positive / negative` arrays for direct use in any bar chart library.
- API: `GET /api/reports/monthly-sentiment?user_id=&year=&month=`.

### Monthly report — KPI analytics & sentiment reporting (`monthly_report_worker.py`)
- **APScheduler-based cron**: Runs day 1 of each month at 06:00 UTC to generate reports for all users.
- **Report payload** includes: KPIs (avg_rating, total_reviews, response_rate_pct, avg_response_time_minutes), business_name, sentiment analysis (top 3 positive + negative concepts).
- **Auto-email**: SendGrid integration notifies users via email when their report is ready (if `SENDGRID_API_KEY` configured).
- **HTML report page** (`/starter/report`): Single-page, print-ready, mobile-responsive report with Chart.js visualizations.
  - KPI cards: rating, review count, AI response rate, avg response time.
  - Rating evolution chart (line).
  - Reviews per month (bar chart with current month highlighted).
  - Word cloud of sentiment concepts (size proportional to mention count).
  - Sentiment concepts bar chart (positive vs negative).

## Quick start (local)

From `backend/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1
```

This installs dependencies, runs migrations, creates a local test user, and starts the API.

## Main endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/api/locations` | List available locations for user (`?user_id=`) — supports zero-friction onboarding |
| `GET` | `/oauth/google/start` | Begin OAuth flow (`user_id`, optional `location_id`) |
| `GET` | `/oauth/google/callback` | OAuth callback — returns JSON or redirects |
| `POST` | `/webhooks/google/reviews` | Pub/Sub push for new reviews |
| `GET` | `/starter/onboarding` | Starter welcome page (Bootstrap) |
| `GET` | `/starter/connect-google` | Redirect to Google OAuth with starter flag |
| `GET` | `/starter/dashboard` | Connection status + last 5 reviews |
| `GET` | `/starter/approvals` | Review approval UI (Bootstrap, `?user_id=`) |
| `GET` | `/starter/report` | Monthly report page (Chart.js, KPI cards, sentiment) (`?user_id=&year=&month=`) |
| `GET` | `/api/reviews/pending` | List pending AUTO_REPLY reviews (`?user_id=`) |
| `POST` | `/api/reviews/{id}/approve` | Send reply to Google + mark as sent |
| `POST` | `/api/reviews/{id}/regenerate` | Re-run NLP, return new suggestion |
| `GET` | `/api/reports/monthly-sentiment` | Top-3 positive/negative concepts (`?user_id=&year=&month=`) |
| `GET` | `/api/reports/monthly` | Stored monthly report payload (`?user_id=&year=&month=`) |
| `GET` | `/api/reports/history` | Historical KPI data for rating evolution (`?user_id=`) |

## Database migrations (Alembic)

| Version | Description |
|---------|-------------|
| `0001` | Initial schema: users, google_connections, reviews |
| `0002` | NLP decision columns on reviews + business_name on connections |
| `0003` | `starter_monthly_metrics` table |
| `0004` | `reply_approved_text` + `reply_sent_at` on reviews |
| `0005` | `monthly_reports` table for persisted monthly KPI reports |

## Running tests

```powershell
# Unit tests (no Docker required)
pytest tests/unit -q

# Integration tests (requires Docker for Postgres)
pytest tests/integration -q
```

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

