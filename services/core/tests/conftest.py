"""
Shared pytest fixtures for the Core Service test suite.

Uses an in-process SQLite (aiosqlite) database so tests run without Docker.
Each test function gets its own isolated session via the ``db`` fixture.
"""

import os
import uuid
from collections.abc import AsyncGenerator

# ── Stub required env vars BEFORE any app module is imported ──────────────────
# config.py instantiates Settings() at module level; if these vars are absent
# (e.g. in CI with no .env file) the import chain fails.  Tests don't use JWT
# verification or RabbitMQ, so dummy values are safe here.
_TEST_PUBLIC_KEY = (
    "-----BEGIN PUBLIC KEY-----\n"
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0000000000000000000000\n"
    "0000000000000000000000000000000000000000000000000000000000000000\n"
    "-----END PUBLIC KEY-----"
)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("RSA_PUBLIC_KEY", _TEST_PUBLIC_KEY)
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import CurrentUser, ProjectMembership
from app.core.database import Base

# ── In-memory async SQLite engine ─────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

AsyncTestSession = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test, drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh AsyncSession for each test."""
    async with AsyncTestSession() as session:
        yield session


# ── Reusable user stubs ───────────────────────────────────────────────────────

@pytest.fixture
def user_alice() -> CurrentUser:
    return CurrentUser(
        id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        name="Alice",
        email="alice@example.com",
    )


@pytest.fixture
def user_bob() -> CurrentUser:
    return CurrentUser(
        id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        name="Bob",
        email="bob@example.com",
    )
