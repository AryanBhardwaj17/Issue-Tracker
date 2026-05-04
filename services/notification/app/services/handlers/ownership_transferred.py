"""Handler for ownership.transferred events."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.events.payloads import OwnershipTransferredPayload
from app.models.notification import DeliveryStatus, EmailDelivery, Notification
from app.services.mailer import send_email
from app.services.template_renderer import render_template

logger = logging.getLogger(__name__)


async def handle_ownership_transferred(
    payload: OwnershipTransferredPayload,
    db: AsyncSession,
    *,
    event_id: str,
) -> None:
    """
    Recipients: the new owner only.

    Actor = the previous owner who transferred. Self-transfer is blocked
    at the API level, so actor_id != new_owner_id always.
    """
    recipient_id = uuid.UUID(payload.new_owner_id)
    recipient_email = payload.new_owner_email
    recipient_name = payload.new_owner_name

    title = f"You are now the owner of {payload.project_name}"
    body = (
        f"{payload.previous_owner_name} transferred ownership of "
        f"\"{payload.project_name}\" to you."
    )
    link = f"/projects/{payload.project_id}/settings"

    # In-app notification — ALWAYS written, even if email fails
    notification = Notification(
        user_id=recipient_id,
        event_type="ownership.transferred",
        title=title,
        body=body,
        link=link,
    )
    db.add(notification)

    # Email delivery audit record
    delivery = EmailDelivery(
        event_type="ownership.transferred",
        recipient_email=recipient_email,
        payload=payload.model_dump(),
        status=DeliveryStatus.PENDING,
    )
    db.add(delivery)
    await db.flush()

    subject = f"[{payload.project_name}] Ownership transferred to you"
    try:
        html = render_template(
            "ownership_transferred.html",
            payload=payload,
            recipient_name=recipient_name,
            link=f"{settings.FRONTEND_URL}{link}",
        )
        await send_email(recipient_email, subject, html)
        delivery.status = DeliveryStatus.SENT
        delivery.sent_at = datetime.now(UTC)
    except Exception as e:
        logger.error(
            "Email failed for ownership.transferred to %s (event_id=%s): %s",
            recipient_email,
            event_id,
            e,
        )
        delivery.status = DeliveryStatus.FAILED
        delivery.error_message = str(e)[:500]
