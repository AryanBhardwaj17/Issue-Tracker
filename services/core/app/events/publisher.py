"""
Event publisher stub — log-and-noop.

When RabbitMQ integration is wired in a later epic, this module will
publish domain events to the message bus.  Until then, it logs the
event payload for debugging.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def publish_event(event_type: str, payload: dict[str, Any]) -> None:
    """Log-and-noop event publisher.  Replace with real broker call later."""
    logger.info("Event [%s]: %s", event_type, payload)
