# Local Development

## 1. Configure backend/.env

Use backend/.env for localhost development. Replace only:
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET

If you use ngrok, also replace:
- GOOGLE_REDIRECT_URI
- GOOGLE_PUBSUB_AUDIENCE
- ALLOWED_HOSTS

## 2. Start locally on Windows PowerShell

From backend:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1
```

This will:
- install Python dependencies
- run Alembic migrations
- create or reuse a local user with email local@example.com
- start Uvicorn on port 8000

## 3. Create a test user manually

```powershell
python .\scripts\create_local_user.py local@example.com
```

The script prints the user_id.

## 4. Local endpoint checks

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/health"
```

```powershell
Invoke-WebRequest -Method Get -Uri "http://localhost:8000/oauth/google/start?user_id=<USER_ID>&location_id=<LOCATION_ID>" -MaximumRedirection 0
```

```powershell
Invoke-WebRequest -Method Post -Uri "http://localhost:8000/webhooks/google/reviews" -ContentType "application/json" -Body "{}"
```

## 5. ngrok for real Google callbacks

```powershell
ngrok http 8000
```

Then update backend/.env with the public ngrok host:
- GOOGLE_REDIRECT_URI=https://<NGROK_HOST>/oauth/google/callback
- GOOGLE_PUBSUB_AUDIENCE=https://<NGROK_HOST>/webhooks/google/reviews
- ALLOWED_HOSTS=localhost,127.0.0.1,<NGROK_HOST>

Restart Uvicorn after changing backend/.env.
