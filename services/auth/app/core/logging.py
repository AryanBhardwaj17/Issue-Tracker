"""
Logging configuration for the auth service.

Call ``configure_logging()`` once at application startup (in ``main.py``
lifespan) before any other code runs so that all loggers inherit the
correct level and format.
"""

import logging
import sys

from app.core.config import settings

# Log format used for all handlers.
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _resolve_log_level(level_name: str) -> int:
    """Safely resolve log level from string with fallback."""
    level_name = level_name.upper()

    if not hasattr(logging, level_name):
        # fallback instead of silent weird behavior
        logging.getLogger(__name__).warning(
            "Invalid LOG_LEVEL '%s', defaulting to INFO", level_name
        )
        return logging.INFO

    return getattr(logging, level_name)


def configure_logging() -> None:
    """Configure the root logger with a consistent format and level."""
    level = _resolve_log_level(settings.LOG_LEVEL)

    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        stream=sys.stdout,
    )

    # Silence noisy third-party loggers
    for noisy in ("asyncio", "sqlalchemy.engine", "sqlalchemy.pool", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).debug(
        "Logging configured (level=%s)", settings.LOG_LEVEL
    )