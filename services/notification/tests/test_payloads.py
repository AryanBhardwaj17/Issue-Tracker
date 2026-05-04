"""Unit tests for inbound event payload Pydantic models."""

import uuid

import pytest
from pydantic import ValidationError

from app.events.payloads import (
    CommentCreatedPayload,
    MemberAddedPayload,
    OwnershipTransferredPayload,
    StoryAssignedPayload,
    StoryUnassignedPayload,
)

from tests.factories import (
    make_comment_created_payload,
    make_member_added_payload,
    make_ownership_transferred_payload,
    make_story_assigned_payload,
    make_story_unassigned_payload,
)


# ── MemberAddedPayload ──────────────────────────────────────────────────────


class TestMemberAddedPayload:
    def test_valid_payload(self):
        data = make_member_added_payload()
        p = MemberAddedPayload.model_validate(data)
        assert p.project_name == "Test Project"
        assert p.added_user_email == "bob@test.com"
        assert p.actor_name == "Alice"

    @pytest.mark.parametrize("missing_field", [
        "project_id", "project_name", "project_key",
        "added_user_id", "added_user_email", "added_user_name",
        "actor_id", "actor_name",
    ])
    def test_missing_required_field(self, missing_field):
        data = make_member_added_payload()
        del data[missing_field]
        with pytest.raises(ValidationError):
            MemberAddedPayload.model_validate(data)

    def test_extra_fields_ignored(self):
        data = make_member_added_payload(unexpected_field="surprise")
        p = MemberAddedPayload.model_validate(data)
        assert not hasattr(p, "unexpected_field")


# ── OwnershipTransferredPayload ──────────────────────────────────────────────


class TestOwnershipTransferredPayload:
    def test_valid_payload(self):
        data = make_ownership_transferred_payload()
        p = OwnershipTransferredPayload.model_validate(data)
        assert p.new_owner_email == "charlie@test.com"
        assert p.previous_owner_name == "Alice"

    @pytest.mark.parametrize("missing_field", [
        "project_id", "project_name",
        "new_owner_id", "new_owner_email", "new_owner_name",
        "previous_owner_id", "previous_owner_name",
        "actor_id",
    ])
    def test_missing_required_field(self, missing_field):
        data = make_ownership_transferred_payload()
        del data[missing_field]
        with pytest.raises(ValidationError):
            OwnershipTransferredPayload.model_validate(data)


# ── StoryAssignedPayload ─────────────────────────────────────────────────────


class TestStoryAssignedPayload:
    def test_valid_payload(self):
        data = make_story_assigned_payload()
        p = StoryAssignedPayload.model_validate(data)
        assert p.story_key == "TP-42"
        assert p.assignee_name == "Bob"

    @pytest.mark.parametrize("missing_field", [
        "project_id", "project_name", "story_id", "story_key", "story_title",
        "assignee_id", "assignee_email", "assignee_name",
        "actor_id", "actor_name",
    ])
    def test_missing_required_field(self, missing_field):
        data = make_story_assigned_payload()
        del data[missing_field]
        with pytest.raises(ValidationError):
            StoryAssignedPayload.model_validate(data)


# ── StoryUnassignedPayload ───────────────────────────────────────────────────


class TestStoryUnassignedPayload:
    def test_valid_payload(self):
        data = make_story_unassigned_payload()
        p = StoryUnassignedPayload.model_validate(data)
        assert p.story_key == "TP-42"
        assert p.previous_assignee_name == "Bob"

    @pytest.mark.parametrize("missing_field", [
        "project_id", "project_name", "story_id", "story_key", "story_title",
        "previous_assignee_id", "previous_assignee_email", "previous_assignee_name",
        "actor_id", "actor_name",
    ])
    def test_missing_required_field(self, missing_field):
        data = make_story_unassigned_payload()
        del data[missing_field]
        with pytest.raises(ValidationError):
            StoryUnassignedPayload.model_validate(data)


# ── CommentCreatedPayload ────────────────────────────────────────────────────


class TestCommentCreatedPayload:
    def test_valid_payload_with_assignee(self):
        data = make_comment_created_payload()
        p = CommentCreatedPayload.model_validate(data)
        assert p.comment_author_name == "Eve"
        assert p.assignee_email == "charlie@test.com"
        assert p.reporter_name == "Bob"

    def test_valid_payload_without_assignee(self):
        """Assignee fields are optional — story may have no assignee."""
        data = make_comment_created_payload(
            assignee_id=None, assignee_email=None, assignee_name=None,
        )
        p = CommentCreatedPayload.model_validate(data)
        assert p.assignee_id is None
        assert p.assignee_email is None
        assert p.assignee_name is None

    def test_assignee_fields_default_to_none(self):
        """When assignee keys are entirely absent, they default to None."""
        data = make_comment_created_payload()
        del data["assignee_id"]
        del data["assignee_email"]
        del data["assignee_name"]
        p = CommentCreatedPayload.model_validate(data)
        assert p.assignee_id is None

    @pytest.mark.parametrize("missing_field", [
        "project_id", "project_name", "story_id", "story_key", "story_title",
        "comment_id", "comment_author_id", "comment_author_name",
        "comment_body_excerpt",
        "reporter_id", "reporter_email", "reporter_name",
    ])
    def test_missing_required_field(self, missing_field):
        data = make_comment_created_payload()
        del data[missing_field]
        with pytest.raises(ValidationError):
            CommentCreatedPayload.model_validate(data)

    def test_extra_fields_ignored(self):
        data = make_comment_created_payload(extra="value")
        p = CommentCreatedPayload.model_validate(data)
        assert not hasattr(p, "extra")

    def test_empty_comment_body_excerpt(self):
        data = make_comment_created_payload(comment_body_excerpt="")
        p = CommentCreatedPayload.model_validate(data)
        assert p.comment_body_excerpt == ""
