"""Shared pytest fixtures for the Notification Service test suite."""

import asyncio
import os

import aio_pika
import pytest

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")


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
def event_loop():
    """Create a session-scoped event loop (required by pytest-asyncio)."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def rabbitmq_url() -> str:
    return RABBITMQ_URL


@pytest.fixture(scope="session", autouse=True)
async def require_rabbitmq():
    """Skip the entire test session if RabbitMQ is not reachable."""
    reachable = await _rabbitmq_reachable()
    if not reachable:
        pytest.skip(
            f"RabbitMQ not reachable at {RABBITMQ_URL} — "
            "start the broker or set RABBITMQ_URL and retry.",
            allow_module_level=True,
        )
