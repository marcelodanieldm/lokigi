# Operations

## Local development (Windows)

From `backend/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1
```

This installs dependencies, migrates DB, creates test user, and starts API.

## Unit tests

```powershell
python -m pytest tests/unit -q --tb=no
```

## Integration tests

```powershell
python -m pytest tests/integration -q --tb=no
```

Note: integration tests depend on Docker/Testcontainers and can be skipped when Docker daemon is unavailable.

## Production deployment

See `backend/deploy/DEPLOYMENT.md` for the full checklist.

Main command from `backend/`:

```bash
./deploy/deploy-prod.sh
```

Post-deploy verification:

```bash
./deploy/verify-post-deploy.sh
```

## Required production environment values

- `DATABASE_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_PUBSUB_AUDIENCE`
- `ALLOWED_HOSTS`
- `APP_DOMAIN`
- `LETSENCRYPT_EMAIL`
- `OAUTH_TOKEN_ENCRYPTION_KEY`
- `OAUTH_STATE_SECRET`
- `WEBHOOK_SHARED_SECRET`

## Alert handling

When review decisions are `ALERT`, the service emits structured warning logs.
Recommended next step is to route these logs to your incident channel (SIEM, Slack, ticketing queue).
