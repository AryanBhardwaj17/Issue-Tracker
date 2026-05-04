"""Handler for member.added events."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.events.payloads import MemberAddedPayload
from app.models.notification import DeliveryStatus, EmailDelivery, Notification
from app.services.mailer import send_email
from app.services.template_renderer import render_template

logger = logging.getLogger(__name__)


async def handle_member_added(
    payload: MemberAddedPayload,
    db: AsyncSession,
    *,
    event_id: str,
) -> None:
    """
    Recipients: the added user only.

    The actor (person who added them) is never the same as the added user,
    so no explicit exclusion check is needed.
    """
    recipient_id = uuid.UUID(payload.added_user_id)
    recipient_email = payload.added_user_email
    recipient_name = payload.added_user_name

    title = f"You've been added to {payload.project_name}"
    body = f'{payload.actor_name} added you to the project "{payload.project_name}".'
    link = f"/projects/{payload.project_id}/board"

    # In-app notification — ALWAYS written, even if email fails
    notification = Notification(
        user_id=recipient_id,
        event_type="member.added",
        title=title,
        body=body,
        link=link,
    )
    db.add(notification)

    # Email delivery audit record
    delivery = EmailDelivery(
        event_type="member.added",
        recipient_email=recipient_email,
        payload=payload.model_dump(),
        status=DeliveryStatus.PENDING,
    )
    db.add(delivery)
    await db.flush()

    subject = f"[{payload.project_key}] You've been added to {payload.project_name}"
    try:
        html = render_template(
            "member_added.html",
            payload=payload,
            recipient_name=recipient_name,
            link=f"{settings.FRONTEND_URL}{link}",
        )
        await send_email(recipient_email, subject, html)
        delivery.status = DeliveryStatus.SENT
        delivery.sent_at = datetime.now(UTC)
    except Exception as e:
        logger.error(
            "Email failed for member.added to %s (event_id=%s): %s",
            recipient_email,
            event_id,
            e,
        )
        delivery.status = DeliveryStatus.FAILED
        delivery.error_message = str(e)[:500]
