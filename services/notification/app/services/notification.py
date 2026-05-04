"""Notification service layer — orchestrates repository + authorization."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, NotYourNotificationError
from app.repositories import notification as repo


async def list_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list, int]:
    """List paginated notifications for the authenticated user."""
    return await repo.get_notifications_for_user(db, user_id, page=page, page_size=page_size)


async def get_unread_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Get unread notification count for the authenticated user."""
    return await repo.get_unread_count(db, user_id)


async def mark_read(db: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID):
    """Mark a single notification as read. Ensures ownership."""
    notification = await repo.get_notification_by_id(db, notification_id)
    if notification is None:
        raise NotFoundError()
    if notification.user_id != user_id:
        raise NotYourNotificationError()
    return await repo.mark_as_read(db, notification)


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Mark all of the user's unread notifications as read."""
    return await repo.mark_all_read_for_user(db, user_id)
