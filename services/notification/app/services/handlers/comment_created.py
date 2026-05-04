"""Handler for comment.created events."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.events.payloads import CommentCreatedPayload
from app.models.notification import DeliveryStatus, EmailDelivery, Notification
from app.services.mailer import send_email
from app.services.template_renderer import render_template

logger = logging.getLogger(__name__)


async def handle_comment_created(
    payload: CommentCreatedPayload,
    db: AsyncSession,
    *,
    event_id: str,
) -> None:
    """
    Recipients: {reporter, assignee} minus {comment_author}.

    Deduplication: if reporter == assignee they receive only one notification.
    If all potential recipients are the author, no notifications are sent.
    """
    author_id = payload.comment_author_id

    # Build recipient set: user_id_str → (email, name)
    # dict preserves insertion order and naturally deduplicates by key
    recipients: dict[str, tuple[str, str]] = {}

    # Reporter (if not the comment author)
    if payload.reporter_id != author_id:
        recipients[payload.reporter_id] = (payload.reporter_email, payload.reporter_name)

    # Assignee (if exists, not the author, and not already added as reporter)
    if (
        payload.assignee_id is not None
        and payload.assignee_id != author_id
        and payload.assignee_id not in recipients
    ):
        recipients[payload.assignee_id] = (payload.assignee_email, payload.assignee_name)

    if not recipients:
        logger.info(
            "comment.created on %s: no recipients after exclusion — skipping (event_id=%s)",
            payload.story_key,
            event_id,
        )
        return

    for user_id_str, (email, name) in recipients.items():
        user_id = uuid.UUID(user_id_str)

        title = f"New comment on {payload.story_key}"
        body_text = (
            f"{payload.comment_author_name} commented on \"{payload.story_title}\": "
            f"{payload.comment_body_excerpt}"
        )
        link = f"/projects/{payload.project_id}/stories/{payload.story_id}"

        # In-app notification — ALWAYS written, even if email fails
        notification = Notification(
            user_id=user_id,
            event_type="comment.created",
            title=title,
            body=body_text,
            link=link,
        )
        db.add(notification)

        # Email delivery audit record (one per recipient)
        delivery = EmailDelivery(
            event_type="comment.created",
            recipient_email=email,
            payload=payload.model_dump(),
            status=DeliveryStatus.PENDING,
        )
        db.add(delivery)
        await db.flush()

        subject = f"[{payload.story_key}] New comment by {payload.comment_author_name}"
        try:
            html = render_template(
                "comment_created.html",
                payload=payload,
                recipient_name=name,
                link=f"{settings.FRONTEND_URL}{link}",
            )
            await send_email(email, subject, html)
            delivery.status = DeliveryStatus.SENT
            delivery.sent_at = datetime.now(UTC)
        except Exception as e:
            logger.error(
                "Email failed for comment.created to %s (event_id=%s): %s",
                email,
                event_id,
                e,
            )
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = str(e)[:500]
