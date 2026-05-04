"""RabbitMQ consumer — connects as a background task, dispatches events."""

import asyncio
import json
import logging
from datetime import UTC, datetime

import aio_pika

from app.core.config import settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "domain-events"
QUEUE_NAME = "notification-service"

# ── Health state (read by the health endpoint) ────────────────────────────────

_consumer_status: str = "disconnected"  # "disconnected" | "connecting" | "connected"
_last_message_at: datetime | None = None
_consumer_task: asyncio.Task | None = None


def get_consumer_status() -> str:
    return _consumer_status


def get_last_message_at() -> datetime | None:
    return _last_message_at


# ── Internal consumer loop ────────────────────────────────────────────────────


async def _consume(dispatch_fn) -> None:  # noqa: ANN001
    """Connect to RabbitMQ, declare topology, and consume messages indefinitely."""
    global _consumer_status, _last_message_at  # noqa: PLW0603

    _consumer_status = "connecting"
    logger.info("Consumer connecting to RabbitMQ at %s", settings.RABBITMQ_URL)

    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Declare durable topic exchange
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Declare durable queue
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)

        # Bind queue to exchange with wildcard routing key
        await queue.bind(exchange, routing_key="#")

        _consumer_status = "connected"
        logger.info(
            "Consumer connected — exchange=%s queue=%s binding=#",
            EXCHANGE_NAME,
            QUEUE_NAME,
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                # Parse envelope
                try:
                    body = json.loads(message.body.decode())
                    event_type: str = body["event_type"]
                    event_id: str = body["event_id"]
                    timestamp: str | None = body.get("timestamp")
                    payload: dict = body["payload"]
                except (json.JSONDecodeError, KeyError) as exc:
                    logger.error(
                        "Consumer: malformed message — acking to discard. error=%s body=%r",
                        exc,
                        message.body[:200],
                    )
                    await message.ack()
                    continue

                # Dispatch
                try:
                    await dispatch_fn(event_type, event_id, timestamp, payload)
                    _last_message_at = datetime.now(UTC)
                    await message.ack()
                    logger.debug("Consumer: acked event_type=%s event_id=%s", event_type, event_id)
                except Exception as exc:  # noqa: BLE001
                    if message.redelivered:
                        # Second failure — ack to avoid infinite loop, log error
                        logger.error(
                            "Consumer: handler failed on redelivered message — acking. "
                            "event_type=%s event_id=%s error=%s",
                            event_type,
                            event_id,
                            exc,
                        )
                        await message.ack()
                    else:
                        # First failure — nack with requeue for one retry
                        logger.warning(
                            "Consumer: handler error — nacking for retry. "
                            "event_type=%s event_id=%s error=%s",
                            event_type,
                            event_id,
                            exc,
                        )
                        await message.nack(requeue=True)


async def _run_with_reconnect(dispatch_fn) -> None:  # noqa: ANN001
    """Wrap _consume so a connection drop doesn't kill the background task."""
    global _consumer_status  # noqa: PLW0603

    while True:
        try:
            await _consume(dispatch_fn)
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled — stopping.")
            _consumer_status = "disconnected"
            return
        except Exception as exc:  # noqa: BLE001
            _consumer_status = "connecting"
            logger.warning("Consumer lost connection: %s — reconnecting in 5 s", exc)
            await asyncio.sleep(5)


# ── Public API ────────────────────────────────────────────────────────────────


async def start_consumer(dispatch_fn) -> None:  # noqa: ANN001
    """Launch the consumer as a non-blocking background task."""
    global _consumer_task  # noqa: PLW0603

    _consumer_task = asyncio.create_task(_run_with_reconnect(dispatch_fn))
    logger.info("Consumer background task started")
    # Yield briefly so the task can begin its first connect attempt
    await asyncio.sleep(0.1)


async def stop_consumer() -> None:
    """Cancel the background consumer task gracefully."""
    global _consumer_task  # noqa: PLW0603

    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
        logger.info("Consumer background task stopped")
    _consumer_task = None
