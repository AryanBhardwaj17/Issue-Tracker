"""
Event publisher — publishes domain events to RabbitMQ via aio-pika.

Design decisions:
- connect() is called at startup. If RabbitMQ is unavailable it logs a WARNING
  and sets _exchange to None — the Core service still boots normally.
- publish_event() is fire-and-forget: failures are WARN-logged and swallowed.
  The API call that triggered the event never fails due to messaging issues.
- Messages are marked PERSISTENT so they survive a RabbitMQ restart.
"""

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import aio_pika

from app.core.config import settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "domain-events"

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_channel: aio_pika.abc.AbstractChannel | None = None
_exchange: aio_pika.abc.AbstractExchange | None = None


async def connect() -> None:
    """
    Open the RabbitMQ connection and declare the topic exchange.

    Called once at application startup. If RabbitMQ is unreachable the error
    is caught, a WARNING is logged, and _exchange remains None so that
    publish_event() silently drops events rather than crashing the service.
    """
    global _connection, _channel, _exchange
    try:
        _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        _channel = await _connection.channel()
        _exchange = await _channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("Event publisher connected to RabbitMQ, exchange '%s' declared", EXCHANGE_NAME)
    except Exception:
        logger.warning(
            "Event publisher failed to connect to RabbitMQ — events will be dropped until "
            "the service is restarted or the connection recovers",
            exc_info=True,
        )
        _connection = None
        _channel = None
        _exchange = None


async def close() -> None:
    """Close the RabbitMQ connection. Called at application shutdown."""
    global _connection, _channel, _exchange
    if _connection is not None:
        try:
            await _connection.close()
            logger.info("Event publisher connection closed")
        except Exception:
            logger.warning("Error while closing event publisher connection", exc_info=True)
        finally:
            _connection = None
            _channel = None
            _exchange = None


async def publish_event(event_type: str, payload: dict[str, Any]) -> None:
    """
    Publish a domain event wrapped in the standard outer envelope.

    Envelope format::

        {
            "event_type": "story.assigned",
            "event_id":   "<uuid4>",
            "timestamp":  "<ISO-8601 UTC>",
            "payload":    { ... }
        }

    If not connected or if the publish fails, logs WARNING and returns.
    The caller's DB transaction is never affected.
    """
    if _exchange is None:
        logger.warning("Event publisher not connected — dropping event [%s]", event_type)
        return

    envelope = {
        "event_type": event_type,
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }

    message = aio_pika.Message(
        body=json.dumps(envelope).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        content_type="application/json",
    )

    try:
        await _exchange.publish(message, routing_key=event_type)
        logger.info("Published event [%s] id=%s", event_type, envelope["event_id"])
    except Exception:
        logger.warning(
            "Failed to publish event [%s] — swallowing to protect caller",
            event_type,
            exc_info=True,
        )
