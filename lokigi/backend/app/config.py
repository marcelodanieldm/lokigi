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

    # Monthly report PDF worker integration
    pdf_worker_enqueue_url: str = ""
    pdf_worker_enqueue_token: str = ""
    pdf_signed_url_ttl_seconds: int = 604800

    # Public domain used in email links (no scheme, no trailing slash)
    app_domain: str = "localhost:8000"

    # Growth scraper (Playwright Python)
    growth_proxy_pool: str = ""
    growth_playwright_timeout_ms: int = 45000
    growth_playwright_headless: bool = True
    growth_playwright_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def parsed_allowed_hosts(self) -> list[str]:
        value = self.allowed_hosts.strip()
        if not value:
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]


settings = Settings()
