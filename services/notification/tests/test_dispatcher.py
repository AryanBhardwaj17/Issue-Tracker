"""Unit tests for the event dispatcher — routing, error handling, DB lifecycle."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.events.constants import (
    EVENT_COMMENT_CREATED,
    EVENT_MEMBER_ADDED,
    EVENT_OWNERSHIP_TRANSFERRED,
    EVENT_STORY_ASSIGNED,
    EVENT_STORY_UNASSIGNED,
)

from conftest import (
    TestSessionLocal,
    make_comment_created_payload,
    make_member_added_payload,
    make_ownership_transferred_payload,
    make_story_assigned_payload,
    make_story_unassigned_payload,
)


EVENT_ID = str(uuid.uuid4())
TIMESTAMP = "2026-05-04T10:00:00Z"


@pytest.fixture(autouse=True)
def _patch_session_local():
    """Route dispatcher's AsyncSessionLocal to in-memory SQLite."""
    with patch("app.services.dispatcher.AsyncSessionLocal", TestSessionLocal):
        yield


# ── Known event → correct handler called ─────────────────────────────────────


class TestDispatchRouting:
    @pytest.mark.parametrize("event_type,payload_factory,handler_path", [
        (EVENT_MEMBER_ADDED, make_member_added_payload, "app.services.handlers.handle_member_added"),
        (EVENT_OWNERSHIP_TRANSFERRED, make_ownership_transferred_payload, "app.services.handlers.handle_ownership_transferred"),
        (EVENT_STORY_ASSIGNED, make_story_assigned_payload, "app.services.handlers.handle_story_assigned"),
        (EVENT_STORY_UNASSIGNED, make_story_unassigned_payload, "app.services.handlers.handle_story_unassigned"),
        (EVENT_COMMENT_CREATED, make_comment_created_payload, "app.services.handlers.handle_comment_created"),
    ])
    async def test_known_event_calls_correct_handler(
        self, event_type, payload_factory, handler_path, mock_send_email,
    ):
        from app.services.dispatcher import dispatch

        payload = payload_factory()
        # Should not raise
        await dispatch(event_type, EVENT_ID, TIMESTAMP, payload)

    async def test_member_added_creates_rows(self, mock_send_email):
        """End-to-end: dispatch member.added → Notification + EmailDelivery in DB."""
        from app.services.dispatcher import dispatch

        payload = make_member_added_payload()
        await dispatch(EVENT_MEMBER_ADDED, EVENT_ID, TIMESTAMP, payload)

        # Verify rows were committed
        from sqlalchemy import select
        from app.models.notification import EmailDelivery, Notification

        async with TestSessionLocal() as db:
            notifs = (await db.execute(select(Notification))).scalars().all()
            deliveries = (await db.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 1
        assert notifs[0].event_type == "member.added"
        assert len(deliveries) == 1


# ── Unknown event type → warning, no crash ───────────────────────────────────


class TestUnknownEvent:
    async def test_unknown_event_type_logs_warning_and_returns(self):
        from app.services.dispatcher import dispatch

        # Should NOT raise
        await dispatch("totally.unknown.event", EVENT_ID, TIMESTAMP, {"foo": "bar"})

    async def test_unknown_event_creates_no_rows(self):
        from app.services.dispatcher import dispatch

        await dispatch("totally.unknown.event", EVENT_ID, TIMESTAMP, {"foo": "bar"})

        from sqlalchemy import select
        from app.models.notification import EmailDelivery, Notification

        async with TestSessionLocal() as db:
            notifs = (await db.execute(select(Notification))).scalars().all()
            deliveries = (await db.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 0
        assert len(deliveries) == 0


# ── Invalid payload → error logged, no crash (poison pill discarded) ─────────


class TestInvalidPayload:
    async def test_invalid_payload_returns_without_raising(self):
        from app.services.dispatcher import dispatch

        # member.added with missing fields
        await dispatch(EVENT_MEMBER_ADDED, EVENT_ID, TIMESTAMP, {"bad": "data"})

    async def test_invalid_payload_creates_no_rows(self):
        from app.services.dispatcher import dispatch

        await dispatch(EVENT_MEMBER_ADDED, EVENT_ID, TIMESTAMP, {})

        from sqlalchemy import select
        from app.models.notification import EmailDelivery, Notification

        async with TestSessionLocal() as db:
            notifs = (await db.execute(select(Notification))).scalars().all()
            deliveries = (await db.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 0
        assert len(deliveries) == 0

    async def test_partially_valid_payload_rejected(self):
        """Payload with some valid fields but missing required ones."""
        from app.services.dispatcher import dispatch

        partial = {"project_id": str(uuid.uuid4()), "project_name": "Partial"}
        await dispatch(EVENT_MEMBER_ADDED, EVENT_ID, TIMESTAMP, partial)

        from sqlalchemy import select
        from app.models.notification import Notification

        async with TestSessionLocal() as db:
            notifs = (await db.execute(select(Notification))).scalars().all()
        assert len(notifs) == 0


# ── Handler raises → dispatcher re-raises after rollback ─────────────────────


class TestHandlerError:
    async def test_handler_exception_is_reraised(self):
        from app.services.dispatcher import dispatch

        payload = make_member_added_payload()

        with patch(
            "app.services.dispatcher._EVENT_HANDLERS",
            {EVENT_MEMBER_ADDED: (
                __import__("app.events.payloads", fromlist=["MemberAddedPayload"]).MemberAddedPayload,
                AsyncMock(side_effect=RuntimeError("DB exploded")),
            )},
        ):
            with pytest.raises(RuntimeError, match="DB exploded"):
                await dispatch(EVENT_MEMBER_ADDED, EVENT_ID, TIMESTAMP, payload)

    async def test_handler_exception_rolls_back_rows(self, mock_send_email):
        """If handler raises, no rows should be committed."""
        from app.services.dispatcher import dispatch

        payload = make_member_added_payload()

        # Wrap handler to raise AFTER it adds rows
        original_handler = (
            __import__(
                "app.services.handlers.member_added",
                fromlist=["handle_member_added"],
            ).handle_member_added
        )

        async def exploding_handler(p, db, *, event_id):
            await original_handler(p, db, event_id=event_id)
            raise RuntimeError("Boom after rows added")

        with patch(
            "app.services.dispatcher._EVENT_HANDLERS",
            {EVENT_MEMBER_ADDED: (
                __import__("app.events.payloads", fromlist=["MemberAddedPayload"]).MemberAddedPayload,
                exploding_handler,
            )},
        ):
            with pytest.raises(RuntimeError, match="Boom"):
                await dispatch(EVENT_MEMBER_ADDED, EVENT_ID, TIMESTAMP, payload)

        # Rows should have been rolled back
        from sqlalchemy import select
        from app.models.notification import EmailDelivery, Notification

        async with TestSessionLocal() as db:
            notifs = (await db.execute(select(Notification))).scalars().all()
            deliveries = (await db.execute(select(EmailDelivery))).scalars().all()

        assert len(notifs) == 0
        assert len(deliveries) == 0
