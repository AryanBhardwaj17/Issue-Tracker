"""
Core Service entry point.

Bootstraps the FastAPI application:
- Lifespan: configure logging on startup, dispose engine on shutdown.
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
from app.schemas.common import ErrorDetail, ErrorEnvelope


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
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
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorEnvelope(message=exc.detail).model_dump(by_alias=True),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
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
