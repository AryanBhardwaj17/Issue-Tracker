"""
Application settings loaded from environment variables / .env file.

All configuration values are defined here and accessed via the module-level
``settings`` singleton. No other module should read environment variables
directly — always import from this module.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    """Pydantic-settings model that reads from the environment or a .env file.

    Fields with defaults are optional in .env; fields without defaults are
    required and will raise a validation error at startup if missing.
    """

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str  

    # ── JWT / RS256 ───────────────────────────────────────────────────────────
    RSA_PRIVATE_KEY: str  # Full PEM string (newlines as \n)
    RSA_PUBLIC_KEY: str  # Full PEM string (newlines as \n)
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "auth-service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    @field_validator("RSA_PRIVATE_KEY", "RSA_PUBLIC_KEY", mode="before")
    @classmethod
    def _expand_pem_newlines(cls, v: str) -> str:
        """Convert literal '\\n' sequences to real newlines in PEM strings."""
        if isinstance(v, str) and "\\n" in v:
            return v.replace("\\n", "\n")
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow extra env vars present in .env without raising an error
        extra="ignore",
    )


# Module-level singleton — import and use ``settings`` everywhere.
settings = Settings()
