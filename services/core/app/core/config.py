"""
Application settings loaded from environment variables / .env file.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic-settings model that reads from the environment or a .env file."""

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str  # postgresql+asyncpg://...

    # ── JWT / RS256 (public key only — Core never signs tokens) ───────────────
    RSA_PUBLIC_KEY: str  # Full PEM string (newlines as \n in env)
    JWT_ALGORITHM: str = "RS256"

    # ── Cross-service ─────────────────────────────────────────────────────────
    AUTH_SERVICE_GRPC_HOST: str = "auth-service:50051"
    INTERNAL_API_KEY: str

    # ── Message bus ───────────────────────────────────────────────────────────
    RABBITMQ_URL: str  # amqp://guest:guest@rabbitmq:5672/

    # ── File uploads ──────────────────────────────────────────────────────────
    UPLOADS_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024

    # ── S3 (AWS only) ─────────────────────────────────────────────────────────
    USE_S3: bool = False  # True on ECS, False for local dev
    S3_BUCKET: str = ""  # e.g. "issuetracker-uploads-prod"
    S3_REGION: str = "us-east-1"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "core-service"
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
