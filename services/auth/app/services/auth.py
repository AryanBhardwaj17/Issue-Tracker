"""
Auth service — business logic for registration, login, token management.

This layer sits between the API routes and the repository layer.  It owns
all auth business rules: name generation, credential verification, token
issuance, and token rotation.  It never touches HTTP concerns (cookies,
headers, status codes) — those belong in the API layer.
"""

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidRefreshTokenError,
    NameGenerationError,
    UserUnavailableError,
)
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories import token as token_repo
from app.repositories import user as user_repo
from app.utils.constants import MAX_NAME_RETRIES, TOKEN_TYPE_BEARER
from app.utils.name import format_display_name, generate_candidate, normalize_name

logger = logging.getLogger(__name__)


# ── Public service functions ──────────────────────────────────────────────────


async def register(
    db: AsyncSession,
    *,
    name: str,
    email: str,
    password: str,
) -> tuple[User, dict]:
    """Register a new user account and issue an initial token pair.

    The display name is canonicalized and a numeric suffix is appended if
    the base name is already taken (Teams-style: "John Doe", "John Doe 1").
    A retry loop handles race conditions where two concurrent registrations
    pick the same candidate.

    Returns:
        A (User, tokens) tuple where tokens contains access_token,
        refresh_token, and token_type.

    Raises:
        EmailAlreadyRegisteredError: If ``email`` is already registered.
        NameGenerationError: If a unique name could not be generated after retries.
    """
    if await user_repo.get_user_by_email(db, email):
        raise EmailAlreadyRegisteredError()

    base_name = format_display_name(name)
    password_hash = hash_password(password)

    for _ in range(MAX_NAME_RETRIES):
        normalized = normalize_name(base_name)
        existing = await user_repo.get_similar_names(db, normalized)
        candidate = generate_candidate(base_name, existing)

        try:
            user = await user_repo.create_user(
                db,
                name=candidate,
                email=email,
                password_hash=password_hash,
            )
            tokens = await _issue_tokens(db, user)
            logger.info("User registered: %s", candidate)
            return user, tokens
        except IntegrityError:
            await db.rollback()
            continue

    raise NameGenerationError()

# ── Internal helpers ──────────────────────────────────────────────────────────


async def _issue_tokens(db: AsyncSession, user: User) -> dict[str, str]:
    """Create and persist a new JWT access token + opaque refresh token pair.

    The raw refresh token is returned to the caller (to be sent to the client);
    only its SHA-256 hash is stored in the database.
    """
    access_token = create_access_token(
        subject=str(user.id),
    )
    raw_refresh = generate_refresh_token()
    await token_repo.create_refresh_token(
        db,
        user_id=user.id,
        token=hash_refresh_token(raw_refresh),
        expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": TOKEN_TYPE_BEARER,
    }


async def login(
    db: AsyncSession,
    *,
    email: str,
    password: str,
) -> tuple[User, dict]:
    """Authenticate a user by email and password, then issue a token pair.
 
    Returns:
        A (User, tokens) tuple on success.
 
    Raises:
        InvalidCredentialsError: If the email does not exist or the
            password does not match.
    """
    from app.core.exceptions import InvalidCredentialsError
 
    user = await user_repo.get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
 
    tokens = await _issue_tokens(db, user)
    logger.info("User logged in: %s", user.email)
    return user, tokens

async def refresh_tokens(db: AsyncSession, *, refresh_token: str) -> dict:
    """Rotate a refresh token — revoke the old one and issue a new pair.
 
    Token rotation limits the window of exposure if a refresh token is stolen.
 
    Args:
        refresh_token: The raw (unhashed) refresh token from the client.
 
    Returns:
        A new tokens dict with access_token, refresh_token, token_type.
 
    Raises:
        InvalidRefreshTokenError: If the token is unknown, revoked, or expired.
        UserUnavailableError: If the owning user no longer exists in the DB.
    """
    hashed = hash_refresh_token(refresh_token)
    record = await token_repo.get_refresh_token(db, hashed)
 
    if not record or record.revoked or record.is_expired:
        raise InvalidRefreshTokenError()
 
    user = await user_repo.get_user_by_id(db, record.user_id)
    if not user:
        raise UserUnavailableError()
 
    await token_repo.revoke_token(db, record)
    return await _issue_tokens(db, user)
 
 
async def logout(db: AsyncSession, *, refresh_token: str) -> None:
    """Revoke a single refresh token.
 
    Silently ignores unknown or already-revoked tokens so that double-logout
    does not surface an error to the client.
    """
    hashed = hash_refresh_token(refresh_token)
    record = await token_repo.get_refresh_token(db, hashed)
    if record and not record.revoked:
        await token_repo.revoke_token(db, record)
 