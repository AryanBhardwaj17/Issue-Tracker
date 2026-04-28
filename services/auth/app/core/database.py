"""
Database engine, session factory, and FastAPI dependency.

All async DB access in the application goes through the ``get_db`` dependency,
which yields a session per request and guarantees commit-on-success /
rollback-on-error behaviour.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models.

    Import this class in every model file so that
    ``Base.metadata`` collects all tables for Alembic and ``create_all``.
    """


# ── Engine ────────────────────────────────────────────────────────────────────
# echo=False always — SQL verbosity is controlled via the sqlalchemy.engine
# logger level in core/logging.py, not by SQLAlchemy's own echo mechanism.
# This prevents duplicate output and respects the Python logging hierarchy.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Drop stale connections before use
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep ORM objects accessible after commit
    autocommit=False,
    autoflush=False,
)


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession]:
    """Yield a database session for the duration of a single request.

    Commits on clean exit; rolls back automatically if an exception is raised.
    Always use this via FastAPI's ``Depends(get_db)`` — never instantiate a
    session directly in route handlers.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
