"""
Structured logging configuration for the Core service.

Call ``configure_logging()`` once at application startup (in ``main.py``
lifespan) before any other code runs so that all loggers inherit the
correct level and format.

Design:
- JSON-formatted logs in production (LOG_FORMAT=json), human-readable in dev.
- Request-correlation via ``X-Request-ID`` header propagated to every log line.
- Noisy third-party loggers silenced to WARNING.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings

# ── Formatters ────────────────────────────────────────────────────────────────

_HUMAN_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line (structured logging)."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Attach request_id if present on the record
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Attach extra fields (e.g. user_id, project_id)
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        # Attach exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


# ── Public API ────────────────────────────────────────────────────────────────


def _resolve_log_level(level_name: str) -> int:
    """Safely resolve log level from string with fallback to INFO."""
    level_name = level_name.upper()
    numeric = getattr(logging, level_name, None)
    if numeric is None:
        logging.getLogger(__name__).warning(
            "Invalid LOG_LEVEL '%s', defaulting to INFO", level_name
        )
        return logging.INFO
    return numeric


def configure_logging() -> None:
    """Configure the root logger with structured format and appropriate level."""
    level = _resolve_log_level(settings.LOG_LEVEL)

    # Remove existing handlers to avoid duplicates on reload
    root = logging.getLogger()
    root.handlers.clear()

    # Choose formatter based on environment
    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(fmt=_HUMAN_FORMAT, datefmt=_DATE_FORMAT))

    root.addHandler(handler)
    root.setLevel(level)

    # Silence noisy third-party loggers
    for noisy in (
        "asyncio",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "uvicorn.access",
        "grpc",
        "hpack",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).debug(
        "Logging configured (level=%s, format=%s)", settings.LOG_LEVEL, settings.LOG_FORMAT
    )
