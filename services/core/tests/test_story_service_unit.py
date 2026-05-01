"""
Unit tests for the story service — transition matrix, guards, and validation.

Uses mocks for DB calls so tests are fast and isolated.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.deps import CurrentUser, ProjectMembership
from app.core.exceptions import BadRequestError, ForbiddenError, StoryNotFoundError, ValidationError
from app.models.story import Priority, StoryStatus, UserStory
from app.services.story import (
    ALLOWED_TRANSITIONS,
    assert_can_delete,
    assert_transition_allowed,
)

# ── Constants ─────────────────────────────────────────────────────────────────

ALICE_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
BOB_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
CHARLIE_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
PROJECT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
STORY_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
EPIC_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")

ALL_STATUSES = [s.value for s in StoryStatus]


# ── Factories ─────────────────────────────────────────────────────────────────


def _user(uid: uuid.UUID = ALICE_ID, name: str = "Alice") -> CurrentUser:
    return CurrentUser(id=uid, name=name, email=f"{name.lower()}@test.com")


def _membership(uid: uuid.UUID = ALICE_ID, role: str = "member") -> ProjectMembership:
    return ProjectMembership(user_id=uid, project_id=PROJECT_ID, name="Alice", role=role)


def _fake_story(
    *,
    reporter_id: uuid.UUID = ALICE_ID,
    assignee_id: uuid.UUID | None = None,
    status: str = "backlog",
) -> MagicMock:
    now = datetime.now(UTC)
    story = MagicMock(spec=UserStory)
    story.id = STORY_ID
    story.project_id = PROJECT_ID
    story.story_key = "PROJ-1"
    story.title = "Test Story"
    story.description = None
    story.epic_id = None
    story.status = StoryStatus(status)
    story.priority = Priority.HIGH
    story.story_points = 3
    story.assignee_id = assignee_id
    story.reporter_id = reporter_id
    story.due_date = None
    story.is_deleted = False
    story.created_at = now
    story.updated_at = now
    return story


# ── Transition Matrix (7×7) ──────────────────────────────────────────────────


class TestTransitionMatrix:
    """Exhaustively test all 7×7 state transitions."""

    def test_same_status_is_always_noop(self):
        """Same-status transitions are always allowed (idempotent no-op)."""
        for status in ALL_STATUSES:
            # Should not raise
            assert_transition_allowed(status, status)

    @pytest.mark.parametrize(
        "old_status,new_status",
        [
            ("backlog", "todo"),
            ("todo", "in_progress"),
            ("todo", "in_review"),
            ("todo", "testing"),
            ("todo", "ready_for_prod"),
            ("todo", "done"),
            ("in_progress", "todo"),
            ("in_progress", "in_review"),
            ("in_progress", "testing"),
            ("in_progress", "ready_for_prod"),
            ("in_progress", "done"),
            ("in_review", "todo"),
            ("in_review", "in_progress"),
            ("in_review", "testing"),
            ("in_review", "ready_for_prod"),
            ("in_review", "done"),
            ("testing", "todo"),
            ("testing", "in_progress"),
            ("testing", "in_review"),
            ("testing", "ready_for_prod"),
            ("testing", "done"),
            ("ready_for_prod", "todo"),
            ("ready_for_prod", "in_progress"),
            ("ready_for_prod", "in_review"),
            ("ready_for_prod", "testing"),
            ("ready_for_prod", "done"),
            ("done", "todo"),
            ("done", "in_progress"),
            ("done", "in_review"),
            ("done", "testing"),
            ("done", "ready_for_prod"),
        ],
    )
    def test_allowed_transitions(self, old_status: str, new_status: str):
        """All explicitly allowed transitions should succeed."""
        assert_transition_allowed(old_status, new_status)

    @pytest.mark.parametrize(
        "old_status",
        ["todo", "in_progress", "in_review", "testing", "ready_for_prod", "done"],
    )
    def test_backlog_regression_blocked(self, old_status: str):
        """No status can transition back to backlog (except backlog itself)."""
        with pytest.raises(BadRequestError, match="Cannot move a committed story back to backlog"):
            assert_transition_allowed(old_status, "backlog")

    @pytest.mark.parametrize(
        "new_status",
        ["in_progress", "in_review", "testing", "ready_for_prod", "done"],
    )
    def test_backlog_only_allows_todo(self, new_status: str):
        """Backlog can only transition to todo."""
        with pytest.raises(BadRequestError):
            assert_transition_allowed("backlog", new_status)

    def test_full_matrix_coverage(self):
        """Every cell in the 7×7 matrix produces either no error or BadRequestError."""
        for old in ALL_STATUSES:
            for new in ALL_STATUSES:
                if old == new:
                    assert_transition_allowed(old, new)
                    continue
                allowed = ALLOWED_TRANSITIONS.get(old, set())
                if new in allowed:
                    assert_transition_allowed(old, new)
                else:
                    with pytest.raises(BadRequestError):
                        assert_transition_allowed(old, new)


# ── Delete Guard ──────────────────────────────────────────────────────────────


class TestDeleteGuard:
    def test_reporter_can_delete(self):
        story = _fake_story(reporter_id=ALICE_ID)
        user = _user(ALICE_ID)
        membership = _membership(ALICE_ID, role="member")
        # Should not raise
        assert_can_delete(story, user, membership)

    def test_owner_can_delete_any(self):
        story = _fake_story(reporter_id=BOB_ID)
        user = _user(ALICE_ID)
        membership = _membership(ALICE_ID, role="owner")
        assert_can_delete(story, user, membership)

    def test_non_reporter_non_owner_cannot_delete(self):
        story = _fake_story(reporter_id=BOB_ID)
        user = _user(CHARLIE_ID)
        membership = _membership(CHARLIE_ID, role="member")
        with pytest.raises(ForbiddenError):
            assert_can_delete(story, user, membership)


# ── Status Auth Rule ──────────────────────────────────────────────────────────


class TestStatusAuthRule:
    """Test that status changes on assigned stories are gated properly."""

    @pytest.mark.asyncio
    async def test_non_assignee_non_owner_cannot_change_status(self):
        """A member who is neither the assignee nor owner gets 403."""
        from app.schemas.story import StoryPatch
        from app.services.story import update_story

        story = _fake_story(
            reporter_id=ALICE_ID,
            assignee_id=BOB_ID,
            status="todo",
        )
        user = _user(CHARLIE_ID, "Charlie")
        membership = _membership(CHARLIE_ID, role="member")
        project = MagicMock()
        project.id = PROJECT_ID
        project.key = "PROJ"
        body = StoryPatch.model_validate({"status": "in_progress"})

        db = AsyncMock()
        db.bind = MagicMock()
        db.bind.dialect.name = "sqlite"

        with pytest.raises(ForbiddenError, match="assignee or the Owner"):
            await update_story(
                db, story=story, project=project, user=user, membership=membership, body=body
            )

    @pytest.mark.asyncio
    async def test_assignee_can_change_status(self):
        """The current assignee can change the status."""
        from app.schemas.story import StoryPatch
        from app.services.story import update_story

        story = _fake_story(
            reporter_id=ALICE_ID,
            assignee_id=BOB_ID,
            status="todo",
        )
        user = _user(BOB_ID, "Bob")
        membership = _membership(BOB_ID, role="member")
        project = MagicMock()
        project.id = PROJECT_ID
        project.key = "PROJ"
        body = StoryPatch.model_validate({"status": "in_progress"})

        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with patch("app.services.story._to_story_out") as mock_out, \
             patch("app.services.story.publish_event") as mock_pub:
            mock_out.return_value = MagicMock()
            await update_story(
                db, story=story, project=project, user=user, membership=membership, body=body
            )
            # Should have committed
            db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_owner_can_change_status_of_assigned_story(self):
        """The project owner can always change status."""
        from app.schemas.story import StoryPatch
        from app.services.story import update_story

        story = _fake_story(
            reporter_id=ALICE_ID,
            assignee_id=BOB_ID,
            status="todo",
        )
        user = _user(CHARLIE_ID, "Charlie")
        membership = _membership(CHARLIE_ID, role="owner")
        project = MagicMock()
        project.id = PROJECT_ID
        project.key = "PROJ"
        body = StoryPatch.model_validate({"status": "in_progress"})

        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with patch("app.services.story._to_story_out") as mock_out, \
             patch("app.services.story.publish_event") as mock_pub:
            mock_out.return_value = MagicMock()
            await update_story(
                db, story=story, project=project, user=user, membership=membership, body=body
            )
            db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unassigned_story_status_change_by_any_member(self):
        """When story has no assignee, any member can change status."""
        from app.schemas.story import StoryPatch
        from app.services.story import update_story

        story = _fake_story(
            reporter_id=ALICE_ID,
            assignee_id=None,
            status="todo",
        )
        user = _user(CHARLIE_ID, "Charlie")
        membership = _membership(CHARLIE_ID, role="member")
        project = MagicMock()
        project.id = PROJECT_ID
        project.key = "PROJ"
        body = StoryPatch.model_validate({"status": "in_progress"})

        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with patch("app.services.story._to_story_out") as mock_out, \
             patch("app.services.story.publish_event"):
            mock_out.return_value = MagicMock()
            await update_story(
                db, story=story, project=project, user=user, membership=membership, body=body
            )
            db.commit.assert_awaited_once()


# ── Empty Patch ───────────────────────────────────────────────────────────────


class TestEmptyPatch:
    @pytest.mark.asyncio
    async def test_empty_patch_raises_400(self):
        """Patching with no fields should raise BadRequestError."""
        from app.schemas.story import StoryPatch
        from app.services.story import update_story

        story = _fake_story()
        body = StoryPatch.model_validate({})  # no fields

        db = AsyncMock()
        user = _user()
        membership = _membership()
        project = MagicMock()
        project.id = PROJECT_ID

        with pytest.raises(BadRequestError, match="No fields to update"):
            await update_story(
                db, story=story, project=project, user=user, membership=membership, body=body
            )


# ── Event Emission ────────────────────────────────────────────────────────────


class TestEventEmission:
    @pytest.mark.asyncio
    async def test_assigned_event_on_assignee_change(self):
        """story.assigned fires when assignee changes to a new user."""
        from app.schemas.story import StoryPatch
        from app.services.story import update_story

        story = _fake_story(assignee_id=None)
        body = StoryPatch.model_validate({"assignee_id": str(BOB_ID)})

        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        user = _user(ALICE_ID)
        membership = _membership(ALICE_ID, role="owner")
        project = MagicMock()
        project.id = PROJECT_ID
        project.key = "PROJ"

        with patch("app.services.story._assert_assignee_is_member") as mock_guard, \
             patch("app.services.story._to_story_out") as mock_out, \
             patch("app.services.story.publish_event") as mock_pub:
            mock_guard.return_value = None
            mock_out.return_value = MagicMock()
            await update_story(
                db, story=story, project=project, user=user, membership=membership, body=body
            )
            mock_pub.assert_awaited_once()
            call_args = mock_pub.call_args
            assert call_args[0][0] == "story.assigned"

    @pytest.mark.asyncio
    async def test_unassigned_event_on_null_assignee(self):
        """story.unassigned fires when assignee is set to null."""
        from app.schemas.story import StoryPatch
        from app.services.story import update_story

        story = _fake_story(assignee_id=BOB_ID)
        body = StoryPatch.model_validate({"assignee_id": None})

        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        user = _user(ALICE_ID)
        membership = _membership(ALICE_ID, role="owner")
        project = MagicMock()
        project.id = PROJECT_ID
        project.key = "PROJ"

        with patch("app.services.story._to_story_out") as mock_out, \
             patch("app.services.story.publish_event") as mock_pub:
            mock_out.return_value = MagicMock()
            await update_story(
                db, story=story, project=project, user=user, membership=membership, body=body
            )
            mock_pub.assert_awaited_once()
            call_args = mock_pub.call_args
            assert call_args[0][0] == "story.unassigned"

    @pytest.mark.asyncio
    async def test_no_event_on_same_assignee(self):
        """No event fires when assigneeId is set to the current value."""
        from app.schemas.story import StoryPatch
        from app.services.story import update_story

        story = _fake_story(assignee_id=BOB_ID)
        body = StoryPatch.model_validate({"assignee_id": str(BOB_ID)})

        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        user = _user(ALICE_ID)
        membership = _membership(ALICE_ID, role="owner")
        project = MagicMock()
        project.id = PROJECT_ID
        project.key = "PROJ"

        with patch("app.services.story._to_story_out") as mock_out, \
             patch("app.services.story.publish_event") as mock_pub:
            mock_out.return_value = MagicMock()
            await update_story(
                db, story=story, project=project, user=user, membership=membership, body=body
            )
            mock_pub.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_event_built_even_when_actor_is_assignee(self):
        """Event payload is built even if the actor assigns themselves."""
        from app.schemas.story import StoryPatch
        from app.services.story import update_story

        story = _fake_story(assignee_id=None)
        body = StoryPatch.model_validate({"assignee_id": str(ALICE_ID)})

        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        user = _user(ALICE_ID)
        membership = _membership(ALICE_ID, role="owner")
        project = MagicMock()
        project.id = PROJECT_ID
        project.key = "PROJ"

        with patch("app.services.story._assert_assignee_is_member") as mock_guard, \
             patch("app.services.story._to_story_out") as mock_out, \
             patch("app.services.story.publish_event") as mock_pub:
            mock_guard.return_value = None
            mock_out.return_value = MagicMock()
            await update_story(
                db, story=story, project=project, user=user, membership=membership, body=body
            )
            # Event still fires — actor-exclusion is done in the consumer
            mock_pub.assert_awaited_once()
            assert mock_pub.call_args[0][0] == "story.assigned"


# ── Search Escaping ───────────────────────────────────────────────────────────


class TestSearchEscaping:
    def test_escape_like_wildcards(self):
        from app.repositories.story import _escape_like

        assert _escape_like("%") == "\\%"
        assert _escape_like("_") == "\\_"
        assert _escape_like("hello%world_") == "hello\\%world\\_"
        assert _escape_like("normal") == "normal"
        assert _escape_like("100%") == "100\\%"

    def test_escape_backslash(self):
        from app.repositories.story import _escape_like

        assert _escape_like("\\") == "\\\\"
