"""Notification Service entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1 import v1_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppException
from app.core.logging import configure_logging
from app.events.consumer import start_consumer, stop_consumer
from app.middleware import LoggingMiddleware, RequestIDFilter, RequestIDMiddleware
from app.services.dispatcher import dispatch


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Configure structured logging first
    configure_logging()

    root = logging.getLogger()
    root.addFilter(RequestIDFilter())

    logger = logging.getLogger(__name__)
    logger.info("Starting %s (debug=%s)", settings.APP_NAME, settings.DEBUG)

    await start_consumer(dispatch)
    logger.info("RabbitMQ consumer background task started")

    yield

    logger.info("Shutting down %s", settings.APP_NAME)
    await stop_consumer()
    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

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
        content={"success": False, "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger = logging.getLogger(__name__)
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
    errors = [
        {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]} for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": "Validation error", "errors": errors},
    )
