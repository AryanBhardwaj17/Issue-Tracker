"""Unit tests for all 5 event handlers — row creation, actor exclusion, dedup, SMTP failure."""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.events.payloads import (
    CommentCreatedPayload,
    MemberAddedPayload,
    OwnershipTransferredPayload,
    StoryAssignedPayload,
    StoryUnassignedPayload,
)
from app.models.notification import DeliveryStatus, EmailDelivery, Notification
from app.services.handlers import (
    handle_comment_created,
    handle_member_added,
    handle_ownership_transferred,
    handle_story_assigned,
    handle_story_unassigned,
)

from tests.factories import (
    make_comment_created_payload,
    make_member_added_payload,
    make_ownership_transferred_payload,
    make_story_assigned_payload,
    make_story_unassigned_payload,
)


EVENT_ID = str(uuid.uuid4())


# ── handle_member_added ──────────────────────────────────────────────────────


class TestHandleMemberAdded:
    async def test_creates_notification_and_delivery(self, db_session, mock_send_email):
        payload = MemberAddedPayload.model_validate(make_member_added_payload())
        await handle_member_added(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 1
        assert notifs[0].event_type == "member.added"
        assert notifs[0].user_id == uuid.UUID(payload.added_user_id)
        assert notifs[0].is_read is False
        assert "/board" in notifs[0].link

        assert len(deliveries) == 1
        assert deliveries[0].recipient_email == payload.added_user_email
        assert deliveries[0].status == DeliveryStatus.SENT

    async def test_email_called_with_correct_subject(self, db_session, mock_send_email):
        data = make_member_added_payload(project_key="PRJ", project_name="My Project")
        payload = MemberAddedPayload.model_validate(data)
        await handle_member_added(payload, db_session, event_id=EVENT_ID)

        mock_send_email["member_added"].assert_awaited_once()
        call_args = mock_send_email["member_added"].call_args
        assert call_args[0][0] == payload.added_user_email
        assert "[PRJ]" in call_args[0][1]
        assert "My Project" in call_args[0][1]

    async def test_smtp_failure_still_creates_notification(self, db_session, mock_send_email):
        mock_send_email["member_added"].side_effect = ConnectionError("SMTP down")
        payload = MemberAddedPayload.model_validate(make_member_added_payload())
        await handle_member_added(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        # Notification ALWAYS written
        assert len(notifs) == 1
        # EmailDelivery exists but with FAILED status
        assert len(deliveries) == 1
        assert deliveries[0].status == DeliveryStatus.FAILED
        assert "SMTP down" in deliveries[0].error_message

    async def test_smtp_error_message_truncated_to_500_chars(self, db_session, mock_send_email):
        long_error = "X" * 1000
        mock_send_email["member_added"].side_effect = RuntimeError(long_error)
        payload = MemberAddedPayload.model_validate(make_member_added_payload())
        await handle_member_added(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()
        assert len(deliveries[0].error_message) == 500


# ── handle_ownership_transferred ─────────────────────────────────────────────


class TestHandleOwnershipTransferred:
    async def test_creates_notification_and_delivery(self, db_session, mock_send_email):
        payload = OwnershipTransferredPayload.model_validate(
            make_ownership_transferred_payload()
        )
        await handle_ownership_transferred(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 1
        assert notifs[0].event_type == "ownership.transferred"
        assert notifs[0].user_id == uuid.UUID(payload.new_owner_id)
        assert "/settings" in notifs[0].link

        assert len(deliveries) == 1
        assert deliveries[0].status == DeliveryStatus.SENT

    async def test_email_subject_format(self, db_session, mock_send_email):
        data = make_ownership_transferred_payload(project_name="Alpha Project")
        payload = OwnershipTransferredPayload.model_validate(data)
        await handle_ownership_transferred(payload, db_session, event_id=EVENT_ID)

        call_args = mock_send_email["ownership_transferred"].call_args
        assert "[Alpha Project]" in call_args[0][1]
        assert "Ownership transferred" in call_args[0][1]


# ── handle_story_assigned ────────────────────────────────────────────────────


class TestHandleStoryAssigned:
    async def test_creates_notification_and_delivery(self, db_session, mock_send_email):
        payload = StoryAssignedPayload.model_validate(make_story_assigned_payload())
        await handle_story_assigned(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 1
        assert notifs[0].event_type == "story.assigned"
        assert notifs[0].user_id == uuid.UUID(payload.assignee_id)

        assert len(deliveries) == 1
        assert deliveries[0].status == DeliveryStatus.SENT

    async def test_self_assign_skips_notification(self, db_session, mock_send_email):
        """assignee == actor → no Notification, no EmailDelivery."""
        actor_id = str(uuid.uuid4())
        data = make_story_assigned_payload(assignee_id=actor_id, actor_id=actor_id)
        payload = StoryAssignedPayload.model_validate(data)
        await handle_story_assigned(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 0
        assert len(deliveries) == 0
        mock_send_email["story_assigned"].assert_not_awaited()

    async def test_email_subject_format(self, db_session, mock_send_email):
        data = make_story_assigned_payload(story_key="PROJ-99")
        payload = StoryAssignedPayload.model_validate(data)
        await handle_story_assigned(payload, db_session, event_id=EVENT_ID)

        call_args = mock_send_email["story_assigned"].call_args
        assert "[PROJ-99]" in call_args[0][1]
        assert "assigned to you" in call_args[0][1]

    async def test_link_includes_story_path(self, db_session, mock_send_email):
        data = make_story_assigned_payload()
        payload = StoryAssignedPayload.model_validate(data)
        await handle_story_assigned(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        assert f"/stories/{payload.story_id}" in notifs[0].link


# ── handle_story_unassigned ──────────────────────────────────────────────────


class TestHandleStoryUnassigned:
    async def test_creates_notification_and_delivery(self, db_session, mock_send_email):
        payload = StoryUnassignedPayload.model_validate(make_story_unassigned_payload())
        await handle_story_unassigned(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 1
        assert notifs[0].event_type == "story.unassigned"
        assert notifs[0].user_id == uuid.UUID(payload.previous_assignee_id)

        assert len(deliveries) == 1
        assert deliveries[0].status == DeliveryStatus.SENT

    async def test_self_unassign_skips_notification(self, db_session, mock_send_email):
        """previous_assignee == actor → no rows, no email."""
        actor_id = str(uuid.uuid4())
        data = make_story_unassigned_payload(
            previous_assignee_id=actor_id, actor_id=actor_id,
        )
        payload = StoryUnassignedPayload.model_validate(data)
        await handle_story_unassigned(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 0
        assert len(deliveries) == 0
        mock_send_email["story_unassigned"].assert_not_awaited()

    async def test_email_subject_format(self, db_session, mock_send_email):
        data = make_story_unassigned_payload(story_key="PROJ-7")
        payload = StoryUnassignedPayload.model_validate(data)
        await handle_story_unassigned(payload, db_session, event_id=EVENT_ID)

        call_args = mock_send_email["story_unassigned"].call_args
        assert "[PROJ-7]" in call_args[0][1]
        assert "unassigned" in call_args[0][1].lower()


# ── handle_comment_created ───────────────────────────────────────────────────


class TestHandleCommentCreated:
    async def test_two_distinct_recipients(self, db_session, mock_send_email):
        """Reporter + assignee (both different from author) → 2 notifications + 2 deliveries."""
        data = make_comment_created_payload()
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 2
        assert len(deliveries) == 2

        user_ids = {n.user_id for n in notifs}
        assert uuid.UUID(payload.reporter_id) in user_ids
        assert uuid.UUID(payload.assignee_id) in user_ids

    async def test_reporter_equals_assignee_dedup(self, db_session, mock_send_email):
        """Reporter == assignee → 1 notification (not 2)."""
        same_id = str(uuid.uuid4())
        data = make_comment_created_payload(
            reporter_id=same_id,
            reporter_email="same@test.com",
            reporter_name="Same Person",
            assignee_id=same_id,
            assignee_email="same@test.com",
            assignee_name="Same Person",
        )
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 1
        assert len(deliveries) == 1

    async def test_author_is_reporter_and_assignee_no_rows(self, db_session, mock_send_email):
        """Author == reporter == assignee → empty recipient set → 0 rows."""
        author_id = str(uuid.uuid4())
        data = make_comment_created_payload(
            comment_author_id=author_id,
            reporter_id=author_id,
            reporter_email="author@test.com",
            reporter_name="Author",
            assignee_id=author_id,
            assignee_email="author@test.com",
            assignee_name="Author",
        )
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 0
        assert len(deliveries) == 0
        mock_send_email["comment_created"].assert_not_awaited()

    async def test_author_is_reporter_only_assignee_notified(self, db_session, mock_send_email):
        """Author == reporter, but assignee is different → 1 notification for assignee."""
        author_id = str(uuid.uuid4())
        assignee_id = str(uuid.uuid4())
        data = make_comment_created_payload(
            comment_author_id=author_id,
            reporter_id=author_id,
            reporter_email="author@test.com",
            reporter_name="Author",
            assignee_id=assignee_id,
            assignee_email="assignee@test.com",
            assignee_name="Assignee",
        )
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        assert len(notifs) == 1
        assert notifs[0].user_id == uuid.UUID(assignee_id)

    async def test_author_is_assignee_only_reporter_notified(self, db_session, mock_send_email):
        """Author == assignee, reporter is different → 1 notification for reporter."""
        author_id = str(uuid.uuid4())
        reporter_id = str(uuid.uuid4())
        data = make_comment_created_payload(
            comment_author_id=author_id,
            reporter_id=reporter_id,
            reporter_email="reporter@test.com",
            reporter_name="Reporter",
            assignee_id=author_id,
            assignee_email="author@test.com",
            assignee_name="Author",
        )
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        assert len(notifs) == 1
        assert notifs[0].user_id == uuid.UUID(reporter_id)

    async def test_no_assignee_only_reporter_notified(self, db_session, mock_send_email):
        """Assignee is None → only reporter gets notified (if != author)."""
        data = make_comment_created_payload(
            assignee_id=None, assignee_email=None, assignee_name=None,
        )
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 1
        assert notifs[0].user_id == uuid.UUID(payload.reporter_id)
        assert len(deliveries) == 1

    async def test_no_assignee_and_author_is_reporter_no_rows(self, db_session, mock_send_email):
        """Assignee is None, author == reporter → 0 rows."""
        author_id = str(uuid.uuid4())
        data = make_comment_created_payload(
            comment_author_id=author_id,
            reporter_id=author_id,
            reporter_email="author@test.com",
            reporter_name="Author",
            assignee_id=None,
            assignee_email=None,
            assignee_name=None,
        )
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        assert len(notifs) == 0

    async def test_smtp_failure_one_recipient_still_creates_notification(
        self, db_session, mock_send_email,
    ):
        """SMTP fails → Notification still created, EmailDelivery status=FAILED."""
        mock_send_email["comment_created"].side_effect = ConnectionError("SMTP unreachable")

        data = make_comment_created_payload(
            assignee_id=None, assignee_email=None, assignee_name=None,
        )
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 1
        assert len(deliveries) == 1
        assert deliveries[0].status == DeliveryStatus.FAILED
        assert "SMTP unreachable" in deliveries[0].error_message

    async def test_smtp_failure_partial_two_recipients(self, db_session, mock_send_email):
        """With 2 recipients and SMTP fails for both — 2 Notifications, 2 FAILED deliveries."""
        mock_send_email["comment_created"].side_effect = ConnectionError("SMTP down")

        data = make_comment_created_payload()
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        deliveries = (await db_session.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 2
        assert len(deliveries) == 2
        assert all(d.status == DeliveryStatus.FAILED for d in deliveries)

    async def test_email_subject_format(self, db_session, mock_send_email):
        data = make_comment_created_payload(
            story_key="PROJ-5",
            comment_author_name="Eve Dev",
            assignee_id=None, assignee_email=None, assignee_name=None,
        )
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)

        call_args = mock_send_email["comment_created"].call_args
        assert "[PROJ-5]" in call_args[0][1]
        assert "Eve Dev" in call_args[0][1]

    async def test_notification_link_includes_story(self, db_session, mock_send_email):
        data = make_comment_created_payload(
            assignee_id=None, assignee_email=None, assignee_name=None,
        )
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        assert f"/stories/{payload.story_id}" in notifs[0].link

    async def test_notification_is_read_defaults_false(self, db_session, mock_send_email):
        data = make_comment_created_payload(
            assignee_id=None, assignee_email=None, assignee_name=None,
        )
        payload = CommentCreatedPayload.model_validate(data)
        await handle_comment_created(payload, db_session, event_id=EVENT_ID)
        await db_session.commit()

        notifs = (await db_session.execute(select(Notification))).scalars().all()
        assert notifs[0].is_read is False
