"""
Refresh-token repository — thin async DB access layer.

Stores and manages SHA-256-hashed opaque refresh tokens.  The raw token is
never passed to or returned from these functions — hashing happens in the
service layer before calling here.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken

logger = logging.getLogger(__name__)


async def create_refresh_token(
    db: AsyncSession,
    *,
    user_id: int,
    token: str,
    expires_days: int = 7,
) -> RefreshToken:
    """Persist a new hashed refresh token and return the ORM instance.

    Args:
        user_id: Owner of the token.
        token: SHA-256 hex digest of the raw opaque token.
        expires_days: Number of days until expiry (default 7).
    """
    expires_at = datetime.now(UTC) + timedelta(days=expires_days)
    record = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
    db.add(record)
    await db.flush()
    await db.refresh(record)
    logger.debug("Refresh token created for user_id=%s", user_id)
    return record


async def get_refresh_token(db: AsyncSession, token: str) -> RefreshToken | None:
    """Return the token record matching the SHA-256 hash ``token``, or None."""
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == token))
    return result.scalar_one_or_none()



