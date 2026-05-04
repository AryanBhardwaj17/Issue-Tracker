"""Tests for the Notification API endpoints (service layer + routing)."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.services import notification as notification_svc


def _make_notification(
    user_id: uuid.UUID,
    *,
    is_read: bool = False,
    title: str = "Test notification",
    body: str = "Test body",
    notification_id: uuid.UUID | None = None,
) -> Notification:
    """Factory for Notification model instances."""
    return Notification(
        id=notification_id or uuid.uuid4(),
        user_id=user_id,
        event_type="story.assigned",
        title=title,
        body=body,
        link="/projects/abc/stories/123",
        is_read=is_read,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
class TestListNotifications:
    async def test_returns_paginated_notifications(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        for i in range(3):
            db_session.add(_make_notification(user_id, title=f"N{i}"))
        await db_session.commit()

        items, total = await notification_svc.list_notifications(
            db_session, user_id, page=1, page_size=10
        )
        assert total == 3
        assert len(items) == 3

    async def test_empty_for_different_user(self, db_session: AsyncSession):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        db_session.add(_make_notification(user_a))
        await db_session.commit()

        items, total = await notification_svc.list_notifications(db_session, user_b)
        assert total == 0
        assert items == []


@pytest.mark.asyncio
class TestGetUnreadCount:
    async def test_returns_correct_count(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        db_session.add(_make_notification(user_id, is_read=False))
        db_session.add(_make_notification(user_id, is_read=True))
        await db_session.commit()

        count = await notification_svc.get_unread_count(db_session, user_id)
        assert count == 1


@pytest.mark.asyncio
class TestMarkRead:
    async def test_marks_own_notification_as_read(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        nid = uuid.uuid4()
        db_session.add(_make_notification(user_id, notification_id=nid, is_read=False))
        await db_session.commit()

        result = await notification_svc.mark_read(db_session, user_id, nid)
        assert result.is_read is True

    async def test_raises_not_found_for_missing_notification(self, db_session: AsyncSession):
        from app.core.exceptions import NotFoundError

        user_id = uuid.uuid4()
        fake_id = uuid.uuid4()

        with pytest.raises(NotFoundError):
            await notification_svc.mark_read(db_session, user_id, fake_id)

    async def test_raises_forbidden_for_other_users_notification(self, db_session: AsyncSession):
        from app.core.exceptions import NotYourNotificationError

        owner = uuid.uuid4()
        attacker = uuid.uuid4()
        nid = uuid.uuid4()
        db_session.add(_make_notification(owner, notification_id=nid))
        await db_session.commit()

        with pytest.raises(NotYourNotificationError):
            await notification_svc.mark_read(db_session, attacker, nid)


@pytest.mark.asyncio
class TestMarkAllRead:
    async def test_marks_all_unread_for_user(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        db_session.add(_make_notification(user_id, is_read=False))
        db_session.add(_make_notification(user_id, is_read=False))
        await db_session.commit()

        updated = await notification_svc.mark_all_read(db_session, user_id)
        assert updated == 2

        count = await notification_svc.get_unread_count(db_session, user_id)
        assert count == 0

    async def test_does_not_affect_other_users(self, db_session: AsyncSession):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        db_session.add(_make_notification(user_a, is_read=False))
        db_session.add(_make_notification(user_b, is_read=False))
        await db_session.commit()

        await notification_svc.mark_all_read(db_session, user_a)
        count = await notification_svc.get_unread_count(db_session, user_b)
        assert count == 1
