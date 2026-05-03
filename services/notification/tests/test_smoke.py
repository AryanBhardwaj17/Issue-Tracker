"""
E5-S1 smoke test: verifies the consumer receives a message published to
the domain-events RabbitMQ exchange.

Requires a live RabbitMQ instance (see conftest.py for skip logic).
"""

import asyncio
import json
import uuid
from datetime import UTC, datetime

import aio_pika
import pytest

from app.events.consumer import (
    get_consumer_status,
    get_last_message_at,
    start_consumer,
    stop_consumer,
)
from app.services.dispatcher import dispatch

EXCHANGE_NAME = "domain-events"
CONSUMER_START_DELAY = 1.5   # seconds to let consumer connect before publishing
MESSAGE_PROCESS_DELAY = 2.0  # seconds to wait for ack after publish


@pytest.mark.rabbitmq
@pytest.mark.asyncio
async def test_consumer_receives_message(rabbitmq_url: str) -> None:
    """
    Publish a test message to the domain-events exchange and assert that
    the consumer processes it (last_message_at becomes non-None).
    """
    # Start the consumer pointing at the real broker
    await start_consumer(dispatch)

    # Give the consumer time to connect
    await asyncio.sleep(CONSUMER_START_DELAY)

    assert get_consumer_status() == "connected", (
        f"Expected consumer status 'connected', got '{get_consumer_status()}'"
    )

    # Record time before publish so we can compare
    before_publish = datetime.now(UTC)

    # Publish a single test message
    connection = await aio_pika.connect(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        payload = {
            "event_type": "test.smoke",
            "event_id": str(uuid.uuid4()),
            "timestamp": before_publish.isoformat(),
            "payload": {"source": "pytest-smoke"},
        }

        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key="test.smoke",
        )

    # Wait for the consumer to ack the message
    await asyncio.sleep(MESSAGE_PROCESS_DELAY)

    last_msg_at = get_last_message_at()
    assert last_msg_at is not None, "Consumer did not process any message within timeout"
    assert last_msg_at >= before_publish, (
        f"last_message_at ({last_msg_at}) predates publish time ({before_publish})"
    )

    await stop_consumer()
