"""
Auth routes — signup, login, refresh, logout.

The refresh token is always set as an HTTP-only cookie and also returned in
the JSON body.  This allows browser clients to use the cookie transparently
while non-browser clients (mobile, CLI) can read the body.
"""

import logging

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import InvalidRefreshTokenError
from app.schemas.auth import AccessTokenResponse, AuthResponse, LoginRequest, RegisterRequest
from app.schemas.common import MessageResponse
from app.services import auth as auth_service
from app.utils.constants import AUTH_COOKIE_PATH, ERR_REFRESH_TOKEN_REQUIRED, REFRESH_TOKEN_COOKIE

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

def _clear_refresh_cookie(response: Response) -> None:
    """Delete the refresh token cookie."""
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path=AUTH_COOKIE_PATH,
    )

# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Register a new user account and issue tokens."""
    print("Signup request:", body.email) 
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

@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Authenticate and issue tokens."""
    user, tokens = await auth_service.login(db, email=body.email, password=body.password)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return AuthResponse(
        user=user,  # type: ignore[arg-type]
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    """Rotate the refresh token and issue a new access token.
 
    Reads the refresh token from the cookie first; falls back to the JSON body
    field ``refresh_token`` if the cookie is absent.
    """
    raw_token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not raw_token:
        try:
            body = await request.json()
            raw_token = body.get("refresh_token")
        except Exception:
            raw_token = None
 
    if not raw_token:
        raise InvalidRefreshTokenError(ERR_REFRESH_TOKEN_REQUIRED)
 
    tokens = await auth_service.refresh_tokens(db, refresh_token=raw_token)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return AccessTokenResponse(access_token=tokens["access_token"])
 
 
@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Revoke the current refresh token and clear the cookie."""
    raw_token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not raw_token:
        try:
            body = await request.json()
            raw_token = body.get("refresh_token")
        except Exception:
            raw_token = None
 
    if raw_token:
        await auth_service.logout(db, refresh_token=raw_token)
 
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully")