"""Tests for the Notification repository layer."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories import notification as repo


def _make_notification(
    user_id: uuid.UUID,
    *,
    is_read: bool = False,
    title: str = "Test notification",
    body: str = "Test body",
) -> Notification:
    """Factory for Notification model instances."""
    return Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        event_type="story.assigned",
        title=title,
        body=body,
        link="/projects/abc/stories/123",
        is_read=is_read,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
class TestGetNotificationsForUser:
    async def test_returns_empty_for_no_notifications(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        notifications, total = await repo.get_notifications_for_user(db_session, user_id)
        assert notifications == []
        assert total == 0

    async def test_returns_paginated_results(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        for i in range(5):
            n = _make_notification(user_id, title=f"Notification {i}")
            db_session.add(n)
        await db_session.commit()

        notifications, total = await repo.get_notifications_for_user(
            db_session, user_id, page=1, page_size=3
        )
        assert total == 5
        assert len(notifications) == 3

    async def test_second_page(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        for i in range(5):
            n = _make_notification(user_id, title=f"Notification {i}")
            db_session.add(n)
        await db_session.commit()

        notifications, total = await repo.get_notifications_for_user(
            db_session, user_id, page=2, page_size=3
        )
        assert total == 5
        assert len(notifications) == 2

    async def test_isolates_by_user(self, db_session: AsyncSession):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        db_session.add(_make_notification(user_a, title="A's notification"))
        db_session.add(_make_notification(user_b, title="B's notification"))
        await db_session.commit()

        notifications, total = await repo.get_notifications_for_user(db_session, user_a)
        assert total == 1
        assert notifications[0].title == "A's notification"


@pytest.mark.asyncio
class TestGetUnreadCount:
    async def test_zero_when_all_read(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        db_session.add(_make_notification(user_id, is_read=True))
        await db_session.commit()

        count = await repo.get_unread_count(db_session, user_id)
        assert count == 0

    async def test_counts_only_unread(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        db_session.add(_make_notification(user_id, is_read=False))
        db_session.add(_make_notification(user_id, is_read=False))
        db_session.add(_make_notification(user_id, is_read=True))
        await db_session.commit()

        count = await repo.get_unread_count(db_session, user_id)
        assert count == 2


@pytest.mark.asyncio
class TestMarkAsRead:
    async def test_marks_notification_read(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        n = _make_notification(user_id, is_read=False)
        db_session.add(n)
        await db_session.commit()

        result = await repo.mark_as_read(db_session, n)
        assert result.is_read is True

    async def test_idempotent_on_already_read(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        n = _make_notification(user_id, is_read=True)
        db_session.add(n)
        await db_session.commit()

        result = await repo.mark_as_read(db_session, n)
        assert result.is_read is True


@pytest.mark.asyncio
class TestMarkAllReadForUser:
    async def test_marks_all_unread(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        db_session.add(_make_notification(user_id, is_read=False))
        db_session.add(_make_notification(user_id, is_read=False))
        db_session.add(_make_notification(user_id, is_read=True))
        await db_session.commit()

        updated = await repo.mark_all_read_for_user(db_session, user_id)
        assert updated == 2

        count = await repo.get_unread_count(db_session, user_id)
        assert count == 0

    async def test_returns_zero_when_none_unread(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        db_session.add(_make_notification(user_id, is_read=True))
        await db_session.commit()

        updated = await repo.mark_all_read_for_user(db_session, user_id)
        assert updated == 0

    async def test_does_not_affect_other_users(self, db_session: AsyncSession):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        db_session.add(_make_notification(user_a, is_read=False))
        db_session.add(_make_notification(user_b, is_read=False))
        await db_session.commit()

        await repo.mark_all_read_for_user(db_session, user_a)
        count = await repo.get_unread_count(db_session, user_b)
        assert count == 1
