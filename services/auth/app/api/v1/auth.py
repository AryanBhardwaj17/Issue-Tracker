"""
Auth routes — signup, login, refresh, logout.

The refresh token is always set as an HTTP-only cookie and also returned in
the JSON body.  This allows browser clients to use the cookie transparently
while non-browser clients (mobile, CLI) can read the body.
"""

import logging

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import (
    AuthResponse,
    RegisterRequest,
)
from app.services import auth as auth_service
from app.utils.constants import AUTH_COOKIE_PATH, REFRESH_TOKEN_COOKIE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Cookie helpers ────────────────────────────────────────────────────────────


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Set the refresh token as a secure HTTP-only cookie."""
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path=AUTH_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )



# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Register a new user account and issue tokens."""
    user, tokens = await auth_service.register(
        db,
        name=body.name,
        email=body.email,
        password=body.password,
    )
    _set_refresh_cookie(response, tokens["refresh_token"])
    return AuthResponse(
        user=user,  # type: ignore[arg-type]
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )