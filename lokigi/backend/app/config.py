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

    # Public domain used in email links (no scheme, no trailing slash)
    app_domain: str = "localhost:8000"

    def parsed_allowed_hosts(self) -> list[str]:
        value = self.allowed_hosts.strip()
        if not value:
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]


settings = Settings()
