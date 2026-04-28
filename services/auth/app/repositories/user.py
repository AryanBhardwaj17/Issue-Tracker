"""
User repository — thin async DB access layer.

All functions here perform a single, well-named DB operation with no business
logic.  Business rules (name generation, password hashing) live exclusively
in the service layer.
"""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


async def create_user(
    db: AsyncSession,
    *,
    name: str,
    email: str,
    password_hash: str,
) -> User:
    """Insert a new user row and return the fully-populated ORM instance.

    Uses ``flush`` (not ``commit``) so the caller's transaction boundary is
    respected — the session is committed by ``get_db`` on clean exit.
    """
    user = User(name=name, email=email, password_hash=password_hash)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("User created: %s (id=%s)", name, user.id)
    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Return the user with ``user_id``, or None if not found."""
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Return the user with ``email``, or None if not found."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_similar_names(db: AsyncSession, normalized_prefix: str) -> list[str]:
    """Return all existing names whose lower-case form starts with ``normalized_prefix``.

    Used by the name generation algorithm to determine the next available suffix.
    """
    stmt = select(User.name).where(func.lower(User.name).like(f"{normalized_prefix}%"))
    result = await db.execute(stmt)
    return list(result.scalars().all())
