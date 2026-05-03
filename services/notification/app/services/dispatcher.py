"""Event dispatcher stub — routes events to handler functions.

Filled out with real handlers in E5-S3.
"""

import logging

logger = logging.getLogger(__name__)


async def dispatch(
    event_type: str,
    event_id: str,
    timestamp: str | None,
    payload: dict,
) -> None:
    """Placeholder dispatcher. Logs the event. Real routing added in E5-S3."""
    logger.info(
        "Dispatch stub: event_type=%s event_id=%s timestamp=%s",
        event_type,
        event_id,
        timestamp,
    )
