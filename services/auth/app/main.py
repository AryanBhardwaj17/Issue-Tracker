"""
FastAPI application entrypoint.

Wires together the lifespan (table creation), global exception handlers, and
router mounting.  This is the only module that imports from every layer — it
is the composition root of the application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import AppException
from app.core.logging import configure_logging
from app.utils.constants import ERR_EMAIL_REGISTERED, ERR_NAME_GENERATION_FAILED

logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup: configure logging, create tables.  Shutdown: dispose engine."""
    configure_logging()
    logger.info("Starting %s", settings.APP_NAME)

    # create_all is only used in development — in production Alembic manages the schema.
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()
    logger.info("Shut down %s", settings.APP_NAME)


# ── App instance ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(v1_router)


# ── Global exception handlers ────────────────────────────────────────────────


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    """Map domain exceptions to HTTP responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
    """Safety net for race-condition duplicate inserts that pass service checks.

    Inspects the underlying DB error message to return a helpful 409 instead
    of a generic 500.
    """
    detail = str(exc.orig) if exc.orig else str(exc)
    if "uq_users_name" in detail:
        return JSONResponse(status_code=409, content={"detail": ERR_NAME_GENERATION_FAILED})
    if "uq_users_email" in detail:
        return JSONResponse(status_code=409, content={"detail": ERR_EMAIL_REGISTERED})
    return JSONResponse(status_code=409, content={"detail": "Duplicate value conflict"})
