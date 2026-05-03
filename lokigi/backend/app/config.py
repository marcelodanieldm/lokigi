from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "lokigi-google-oauth"
    app_env: str = "dev"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/lokigi"

    oauth_state_secret: str = "change-me-in-production"
    oauth_token_encryption_key: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/oauth/google/callback"

    google_pubsub_audience: str = ""
    allowed_hosts: str = "*"
    webhook_shared_secret: str = ""
    negative_review_alert_webhook_url: str = ""
    negative_review_alert_webhook_token: str = ""

    # SendGrid — leave empty to disable email sending
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@lokigi.com"

    # Stripe billing
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_growth_price_id: str = ""
    stripe_growth_checkout_url: str = ""

    # Optional LLM provider for Starter Tip-of-Day (OpenAI-compatible API)
    tip_llm_enabled: bool = False
    tip_llm_api_base: str = "https://api.openai.com/v1"
    tip_llm_api_key: str = ""
    tip_llm_model: str = "gpt-4o-mini"

    # Optional LLM provider for Google review reply drafts
    review_reply_llm_enabled: bool = False
    review_reply_llm_api_base: str = "https://api.openai.com/v1"
    review_reply_llm_api_key: str = ""
    review_reply_llm_model: str = "gpt-4o-mini"

    # Monthly report PDF worker integration
    pdf_worker_enqueue_url: str = ""
    pdf_worker_enqueue_token: str = ""
    pdf_signed_url_ttl_seconds: int = 604800

    # Public domain used in email links (no scheme, no trailing slash)
    app_domain: str = "localhost:8000"

    # Google Maps / Places API (Onboarding business search)
    google_maps_api_key: str = ""

    # Growth scraper (Playwright Python)
    growth_proxy_pool: str = ""
    growth_playwright_timeout_ms: int = 45000
    growth_playwright_headless: bool = True
    growth_playwright_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    # CEO Command Center — set a long random secret in production
    ceo_api_key: str = "change-me-in-production-ceo"

    # Redis (for CEO financial KPI cache)
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_audience: str = ""

    # Enterprise onboarding — local asset uploads
    assets_upload_dir: str = "assets/uploads"

    # Auth / Login system
    jwt_access_token_expire_hours: int = 8
    totp_issuer: str = "Lokigi"
    # Comma-separated IPv4/IPv6 allowed for CEO login. Empty = allow all (dev only).
    ceo_allowed_ips: str = ""
    login_max_attempts: int = 5
    login_lockout_minutes: int = 30
    # Google OAuth2 for user login (openid email profile)
    google_login_redirect_uri: str = "http://localhost:8000/auth/callback"
    # Session cookie config
    session_cookie_secure: bool = False  # Set True in production (HTTPS)
    session_cookie_samesite: str = "lax"

    def parsed_allowed_hosts(self) -> list[str]:
        value = self.allowed_hosts.strip()
        if not value:
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]


settings = Settings()
