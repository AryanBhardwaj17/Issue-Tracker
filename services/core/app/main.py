"""
Core Service entry point.

Bootstraps the FastAPI application:
- Lifespan: configure structured logging on startup, dispose engine on shutdown.
- Request-ID and logging middleware for observability.
- CORS middleware.
- API v1 router mounted at /api/v1.
- Global exception handlers for AppException and RequestValidationError.
- Health check at GET /api/v1/health.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import v1_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppException
from app.core.logging import configure_logging
from app.grpc.client import AuthGrpcClient
from app.middleware import LoggingMiddleware, RequestIDFilter, RequestIDMiddleware
from app.schemas.common import ErrorDetail, ErrorEnvelope

# Singleton gRPC client — set in lifespan, accessed via get_grpc_client() in deps.
_grpc_client: AuthGrpcClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    global _grpc_client  # noqa: PLW0603

    # Configure structured logging before anything else
    configure_logging()

    # Attach request-ID filter to root logger so all log records get it
    root = logging.getLogger()
    root.addFilter(RequestIDFilter())

    logger = logging.getLogger(__name__)
    logger.info("Starting %s (debug=%s)", settings.APP_NAME, settings.DEBUG)

    _grpc_client = AuthGrpcClient()
    await _grpc_client.connect()
    logger.info("gRPC client connected to %s", settings.AUTH_SERVICE_GRPC_HOST)

    yield

    logger.info("Shutting down %s", settings.APP_NAME)
    await _grpc_client.close()
    _grpc_client = None
    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ── Middleware (order matters: outermost first) ───────────────────────────────
# RequestID must be outermost so the ID is available for the logging middleware.
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(v1_router, prefix="/api/v1")


# ── Exception handlers ────────────────────────────────────────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger = logging.getLogger(__name__)
    logger.warning(
        "AppException: %s (status=%d, path=%s)",
        exc.detail,
        exc.status_code,
        request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorEnvelope(message=exc.detail).model_dump(by_alias=True),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger = logging.getLogger(__name__)
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
    errors = [
        ErrorDetail(
            field=".".join(str(loc) for loc in e["loc"]),
            message=e["msg"],
        )
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorEnvelope(message="Validation error", errors=errors).model_dump(by_alias=True),
    )


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/v1/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": settings.APP_NAME}

