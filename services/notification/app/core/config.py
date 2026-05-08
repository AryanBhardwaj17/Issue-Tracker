"""Application settings loaded from environment variables / .env file."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic-settings model that reads from the environment or a .env file."""

    # ── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str  # postgresql+asyncpg://...

    # ── JWT / RS256 (public key only — Notification never signs tokens) ──────────
    RSA_PUBLIC_KEY: str  # Full PEM string (newlines as \n in env)
    JWT_ALGORITHM: str = "RS256"

    # ── Message bus ─────────────────────────────────────────────────────────
    RABBITMQ_URL: str  # amqps://user:pass@broker.mq.region.amazonaws.com:5671

    # ── Email (SMTP) ────────────────────────────────────────────────────────
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@issuetracker.dev"
    SMTP_USE_TLS: bool = False
    SMTP_VALIDATE_CERTS: bool = True  # False for local MailHog, True for SendGrid

    # ── Frontend URL (used in email links) ──────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Application ────────────────────────────────────────────────────────
    APP_NAME: str = "notification-service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" for production, "text" for local dev

    @field_validator("RSA_PUBLIC_KEY", mode="before")
    @classmethod
    def _expand_pem_newlines(cls, v: str) -> str:
        """Convert literal '\\n' sequences to real newlines in PEM strings."""
        if isinstance(v, str) and "\\n" in v:
            return v.replace("\\n", "\n")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
