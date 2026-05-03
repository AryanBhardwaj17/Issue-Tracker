"""
Middleware for the Core service.

- RequestIDMiddleware: generates/propagates X-Request-ID for every request
  and injects it into logs via a context variable.
- LoggingMiddleware: logs request start/finish with timing.
"""

import contextvars
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context var holds the current request ID — accessible from any logger.
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

logger = logging.getLogger(__name__)


class RequestIDFilter(logging.Filter):
    """Inject request_id from context var into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get("-")  # type: ignore[attr-defined]
        return True


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Propagate or generate an X-Request-ID header.

    - If the client sends X-Request-ID, reuse it.
    - Otherwise generate a UUID4.
    - Set it on the response header and in the context var for logging.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = request.headers.get("x-request-id")
        rid = incoming_id if incoming_id else str(uuid.uuid4())
        request_id_ctx.set(rid)

        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        method = request.method
        path = request.url.path

        # Skip health check noise
        if path == "/api/v1/health":
            return await call_next(request)

        logger.info(
            "Request started: %s %s",
            method,
            path,
            extra={"extra_data": {"method": method, "path": path}},
        )

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Request finished: %s %s -> %d (%.1fms)",
            method,
            path,
            response.status_code,
            duration_ms,
            extra={
                "extra_data": {
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            },
        )

        return response
