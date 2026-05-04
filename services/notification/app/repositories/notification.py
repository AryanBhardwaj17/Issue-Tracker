"""Repository layer — notification queries."""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def get_notifications_for_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[Notification], int]:
    """Return paginated notifications for a user, newest first."""
    offset = (page - 1) * page_size

    count_q = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    total = (await db.execute(count_q)).scalar_one()

    rows_q = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(rows_q)
    notifications = list(result.scalars().all())

    return notifications, total


async def get_unread_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Return number of unread notifications for a user."""
    q = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
    )
    return (await db.execute(q)).scalar_one()


async def get_notification_by_id(
    db: AsyncSession, notification_id: uuid.UUID
) -> Notification | None:
    """Fetch a single notification by ID."""
    q = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(q)
    return result.scalar_one_or_none()


async def mark_as_read(db: AsyncSession, notification: Notification) -> Notification:
    """Mark a single notification as read."""
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_read_for_user(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Mark all unread notifications for a user as read. Returns count updated."""
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
