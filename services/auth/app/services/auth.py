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
)
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
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
