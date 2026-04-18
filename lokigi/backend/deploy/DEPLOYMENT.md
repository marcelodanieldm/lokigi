# Deploy Guide

## Exact .env.production values

Use these values in backend/.env.production:

- APP_NAME: lokigi-google-oauth
- APP_ENV: production
- DATABASE_URL: postgresql+psycopg://<db_user>:<db_password>@<db_host>:5432/<db_name>?sslmode=require
- OAUTH_TOKEN_ENCRYPTION_KEY: generated Fernet key already created locally
- OAUTH_STATE_SECRET: generated secret already created locally
- WEBHOOK_SHARED_SECRET: generated secret already created locally
- GOOGLE_CLIENT_ID: value from Google Cloud Console > APIs & Services > Credentials > OAuth 2.0 Client IDs > Client ID
- GOOGLE_CLIENT_SECRET: value from the same OAuth 2.0 Client ID > Client secret
- GOOGLE_REDIRECT_URI: exact public callback URL, for example https://api.yourdomain.com/oauth/google/callback
- GOOGLE_PUBSUB_AUDIENCE: exact audience configured in the Pub/Sub push subscription OIDC token. Recommended: https://api.yourdomain.com/webhooks/google/reviews
- ALLOWED_HOSTS: exact hostname list accepted by FastAPI TrustedHostMiddleware. Example: api.yourdomain.com
- APP_DOMAIN: exact public hostname served by Caddy. Example: api.yourdomain.com
- LETSENCRYPT_EMAIL: operational email used by Let's Encrypt. Example: ops@yourdomain.com

## Google Cloud values walkthrough

### 1. OAuth client

In Google Cloud Console:
- Go to APIs & Services > Credentials.
- Create or open an OAuth 2.0 Client ID of type Web application.
- Add this Authorized redirect URI exactly:
  - https://api.yourdomain.com/oauth/google/callback
- Copy Client ID into GOOGLE_CLIENT_ID.
- Copy Client Secret into GOOGLE_CLIENT_SECRET.

### 2. Business Profile access

In the same Google Cloud project:
- Enable the APIs required by Business Profile.
- The app must request scope https://www.googleapis.com/auth/business.manage.
- The Google account that authorizes must have access to the target Business Profile location.

### 3. Pub/Sub push webhook

For the Pub/Sub push subscription that sends review notifications:
- Push endpoint: https://api.yourdomain.com/webhooks/google/reviews
- Authentication: OIDC token enabled.
- Audience: set it exactly to https://api.yourdomain.com/webhooks/google/reviews
- Use that same exact string in GOOGLE_PUBSUB_AUDIENCE.

## Exact deploy command on the server

From the backend directory on the target Linux server:

```bash
chmod +x deploy/deploy-prod.sh deploy/verify-post-deploy.sh
./deploy/deploy-prod.sh
```

Equivalent raw command:

```bash
docker compose --env-file .env.production -f deploy/docker-compose.prod.yml up -d --build
```

## Post-deploy verification

Run:

```bash
./deploy/verify-post-deploy.sh
```

This verifies:
- https://APP_DOMAIN/health returns 200
- https://APP_DOMAIN/webhooks/google/reviews is publicly reachable and returns an expected non-success status without credentials
- a TLS certificate is presented on port 443 and its subject, issuer, and validity dates are readable
