"""Shared pytest fixtures for the Notification Service test suite."""

import asyncio
import os
from unittest.mock import AsyncMock, patch

# Set test env vars BEFORE any app imports (mailer validates MAIL_FROM at import time)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("SMTP_FROM", "noreply@issuetracker.dev")

import aio_pika
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.notification import DeliveryStatus, EmailDelivery, Notification  # noqa: F401

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

# ── In-memory SQLite for unit tests ──────────────────────────────────────────

_test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
TestSessionLocal = async_sessionmaker(
    bind=_test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True)
async def _setup_db():
    """Create all tables before each test, drop after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # SQLite doesn't support real UUID columns — map them to CHAR(32)
    # The ORM models use uuid.uuid4 defaults which work fine with SQLite's
    # text affinity, so no further adaptation is needed.

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def db_session() -> AsyncSession:
    """Provide a clean async DB session for handler tests."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture()
def mock_send_email():
    """Patch mailer.send_email with an AsyncMock. Yields the mock."""
    with patch("app.services.handlers.member_added.send_email", new_callable=AsyncMock) as m1, \
         patch("app.services.handlers.ownership_transferred.send_email", new_callable=AsyncMock) as m2, \
         patch("app.services.handlers.story_assigned.send_email", new_callable=AsyncMock) as m3, \
         patch("app.services.handlers.story_unassigned.send_email", new_callable=AsyncMock) as m4, \
         patch("app.services.handlers.comment_created.send_email", new_callable=AsyncMock) as m5:
        # Return a dict so tests can check the specific handler's mock
        yield {
            "member_added": m1,
            "ownership_transferred": m2,
            "story_assigned": m3,
            "story_unassigned": m4,
            "comment_created": m5,
        }


# ── RabbitMQ helpers (for smoke/integration tests only) ──────────────────────

async def _rabbitmq_reachable() -> bool:
    """Return True if RabbitMQ is reachable, False otherwise."""
    try:
        connection = await asyncio.wait_for(
            aio_pika.connect(RABBITMQ_URL),  # plain connect, not connect_robust
            timeout=3,
        )
        await connection.close()
        return True
    except Exception:  # noqa: BLE001
        return False


def pytest_configure(config):  # noqa: ANN001
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "rabbitmq: marks tests that require a live RabbitMQ instance",
    )


@pytest.fixture(scope="session")
def rabbitmq_url() -> str:
    return RABBITMQ_URL
