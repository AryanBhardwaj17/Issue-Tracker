"""Handler for story.unassigned events."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.events.payloads import StoryUnassignedPayload
from app.models.notification import DeliveryStatus, EmailDelivery, Notification
from app.services.mailer import send_email
from app.services.template_renderer import render_template

logger = logging.getLogger(__name__)


async def handle_story_unassigned(
    payload: StoryUnassignedPayload,
    db: AsyncSession,
    *,
    event_id: str,
) -> None:
    """
    Recipients: the previous assignee.

    Skipped entirely if previous_assignee == actor (user unassigned themselves).
    """
    if payload.previous_assignee_id == payload.actor_id:
        logger.info(
            "story.unassigned: previous_assignee == actor (%s)"
            " — skipping notification (event_id=%s)",
            payload.actor_id,
            event_id,
        )
        return

    recipient_id = uuid.UUID(payload.previous_assignee_id)
    recipient_email = payload.previous_assignee_email
    recipient_name = payload.previous_assignee_name

    title = f"Story unassigned: {payload.story_key}"
    body = (
        f'{payload.actor_name} unassigned you from "{payload.story_title}" '
        f"in {payload.project_name}."
    )
    link = f"/projects/{payload.project_id}/stories/{payload.story_id}"

    # In-app notification — ALWAYS written, even if email fails
    notification = Notification(
        user_id=recipient_id,
        event_type="story.unassigned",
        title=title,
        body=body,
        link=link,
    )
    db.add(notification)

    # Email delivery audit record
    delivery = EmailDelivery(
        event_type="story.unassigned",
        recipient_email=recipient_email,
        payload=payload.model_dump(),
        status=DeliveryStatus.PENDING,
    )
    db.add(delivery)
    await db.flush()

    subject = f"[{payload.story_key}] You've been unassigned"
    try:
        html = render_template(
            "story_unassigned.html",
            payload=payload,
            recipient_name=recipient_name,
            link=f"{settings.FRONTEND_URL}{link}",
        )
        await send_email(recipient_email, subject, html)
        delivery.status = DeliveryStatus.SENT
        delivery.sent_at = datetime.now(UTC)
    except Exception as e:
        logger.error(
            "Email failed for story.unassigned to %s (event_id=%s): %s",
            recipient_email,
            event_id,
            e,
        )
        delivery.status = DeliveryStatus.FAILED
        delivery.error_message = str(e)[:500]
