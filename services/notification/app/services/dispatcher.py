"""Event dispatcher — routes consumed events to handler functions by event_type."""

import logging

from app.core.database import AsyncSessionLocal
from app.events.constants import (
    EVENT_COMMENT_CREATED,
    EVENT_MEMBER_ADDED,
    EVENT_OWNERSHIP_TRANSFERRED,
    EVENT_STORY_ASSIGNED,
    EVENT_STORY_UNASSIGNED,
)
from app.events.payloads import (
    CommentCreatedPayload,
    MemberAddedPayload,
    OwnershipTransferredPayload,
    StoryAssignedPayload,
    StoryUnassignedPayload,
)
from app.services.handlers import (
    handle_comment_created,
    handle_member_added,
    handle_ownership_transferred,
    handle_story_assigned,
    handle_story_unassigned,
)

logger = logging.getLogger(__name__)

# Map event_type → (Pydantic model class, async handler function)
_EVENT_HANDLERS: dict[str, tuple[type, object]] = {
    EVENT_MEMBER_ADDED: (MemberAddedPayload, handle_member_added),
    EVENT_OWNERSHIP_TRANSFERRED: (OwnershipTransferredPayload, handle_ownership_transferred),
    EVENT_STORY_ASSIGNED: (StoryAssignedPayload, handle_story_assigned),
    EVENT_STORY_UNASSIGNED: (StoryUnassignedPayload, handle_story_unassigned),
    EVENT_COMMENT_CREATED: (CommentCreatedPayload, handle_comment_created),
}


async def dispatch(
    event_type: str,
    event_id: str,
    timestamp: str | None,
    payload: dict,
) -> None:
    """
    Parse the raw payload, open a DB session, call the handler, and commit.

    - Unknown event_type → log warning, return (consumer acks — no crash)
    - Payload validation error → log error, return (consumer acks — poison pill discarded)
    - Handler exception → rollback, re-raise (consumer nacks for one retry)
    """
    handler_entry = _EVENT_HANDLERS.get(event_type)
    if handler_entry is None:
        logger.warning(
            "Unknown event_type '%s' — skipping (event_id=%s)", event_type, event_id
        )
        return

    model_cls, handler_fn = handler_entry

    try:
        parsed = model_cls.model_validate(payload)
    except Exception:
        logger.exception(
            "Failed to parse payload for event [%s] id=%s — discarding (poison pill)",
            event_type,
            event_id,
        )
        return  # Don't re-raise — let consumer ack

    async with AsyncSessionLocal() as db:
        try:
            await handler_fn(parsed, db, event_id=event_id)
            await db.commit()
            logger.info(
                "Dispatched event [%s] id=%s — committed", event_type, event_id
            )
        except Exception:
            await db.rollback()
            logger.exception(
                "Handler failed for event [%s] id=%s — rolled back", event_type, event_id
            )
            raise  # Re-raise so consumer nacks for retry
