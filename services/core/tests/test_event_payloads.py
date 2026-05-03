"""
Unit tests for event payload builders.

Verifies:
- Each builder returns exactly the key set specified in LLD §9.1 (no extra, no missing).
- All UUID-typed arguments are serialised to strings in the output.
- ``comment_body_excerpt`` is capped at 200 chars.
- Nullable fields (assignee) behave correctly for both None and non-None inputs.
- No external I/O — pure dict-in / dict-out tests.
"""

import uuid

from app.events.payloads import (
    build_comment_created_payload,
    build_member_added_payload,
    build_ownership_transferred_payload,
    build_story_assigned_payload,
    build_story_unassigned_payload,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

PROJECT_ID = uuid.uuid4()
STORY_ID = uuid.uuid4()
COMMENT_ID = uuid.uuid4()
ACTOR_ID = uuid.uuid4()
ASSIGNEE_ID = uuid.uuid4()
REPORTER_ID = uuid.uuid4()
NEW_OWNER_ID = uuid.uuid4()
ADDED_USER_ID = uuid.uuid4()


# ── member.added ──────────────────────────────────────────────────────────────


class TestBuildMemberAddedPayload:
    def _build(self, **overrides):
        defaults = dict(
            project_id=PROJECT_ID,
            project_name="Shop Front",
            project_key="SHOP",
            added_user_id=ADDED_USER_ID,
            added_user_email="bob@example.com",
            added_user_name="Bob Ops",
            actor_id=ACTOR_ID,
            actor_name="Jane Dev",
        )
        return build_member_added_payload(**{**defaults, **overrides})

    def test_exact_keys(self):
        payload = self._build()
        expected_keys = {
            "project_id",
            "project_name",
            "project_key",
            "added_user_id",
            "added_user_email",
            "added_user_name",
            "actor_id",
            "actor_name",
        }
        assert set(payload.keys()) == expected_keys

    def test_uuids_are_strings(self):
        payload = self._build()
        assert isinstance(payload["project_id"], str)
        assert isinstance(payload["added_user_id"], str)
        assert isinstance(payload["actor_id"], str)

    def test_uuid_values_match(self):
        payload = self._build()
        assert payload["project_id"] == str(PROJECT_ID)
        assert payload["added_user_id"] == str(ADDED_USER_ID)
        assert payload["actor_id"] == str(ACTOR_ID)

    def test_string_fields(self):
        payload = self._build()
        assert payload["project_name"] == "Shop Front"
        assert payload["project_key"] == "SHOP"
        assert payload["added_user_email"] == "bob@example.com"
        assert payload["added_user_name"] == "Bob Ops"
        assert payload["actor_name"] == "Jane Dev"


# ── ownership.transferred ────────────────────────────────────────────────────


class TestBuildOwnershipTransferredPayload:
    def _build(self, **overrides):
        defaults = dict(
            project_id=PROJECT_ID,
            project_name="Shop Front",
            new_owner_id=NEW_OWNER_ID,
            new_owner_email="bob@example.com",
            new_owner_name="Bob Ops",
            previous_owner_id=ACTOR_ID,
            previous_owner_name="Jane Dev",
            actor_id=ACTOR_ID,
        )
        return build_ownership_transferred_payload(**{**defaults, **overrides})

    def test_exact_keys(self):
        payload = self._build()
        expected_keys = {
            "project_id",
            "project_name",
            "new_owner_id",
            "new_owner_email",
            "new_owner_name",
            "previous_owner_id",
            "previous_owner_name",
            "actor_id",
        }
        assert set(payload.keys()) == expected_keys

    def test_uuids_are_strings(self):
        payload = self._build()
        for key in ("project_id", "new_owner_id", "previous_owner_id", "actor_id"):
            assert isinstance(payload[key], str), f"{key} should be a string"

    def test_values(self):
        payload = self._build()
        assert payload["project_name"] == "Shop Front"
        assert payload["new_owner_email"] == "bob@example.com"
        assert payload["previous_owner_name"] == "Jane Dev"


# ── story.assigned ────────────────────────────────────────────────────────────


class TestBuildStoryAssignedPayload:
    def _build(self, **overrides):
        defaults = dict(
            project_id=PROJECT_ID,
            project_name="Shop Front",
            story_id=STORY_ID,
            story_key="SHOP-42",
            story_title="Add checkout button",
            assignee_id=ASSIGNEE_ID,
            assignee_email="bob@example.com",
            assignee_name="Bob Ops",
            actor_id=ACTOR_ID,
            actor_name="Jane Dev",
        )
        return build_story_assigned_payload(**{**defaults, **overrides})

    def test_exact_keys(self):
        payload = self._build()
        expected_keys = {
            "project_id",
            "project_name",
            "story_id",
            "story_key",
            "story_title",
            "assignee_id",
            "assignee_email",
            "assignee_name",
            "actor_id",
            "actor_name",
        }
        assert set(payload.keys()) == expected_keys

    def test_uuids_are_strings(self):
        payload = self._build()
        for key in ("project_id", "story_id", "assignee_id", "actor_id"):
            assert isinstance(payload[key], str)

    def test_values(self):
        payload = self._build()
        assert payload["project_name"] == "Shop Front"
        assert payload["story_key"] == "SHOP-42"
        assert payload["assignee_email"] == "bob@example.com"
        assert payload["assignee_name"] == "Bob Ops"
        assert payload["actor_name"] == "Jane Dev"


# ── story.unassigned ──────────────────────────────────────────────────────────


class TestBuildStoryUnassignedPayload:
    def _build(self, **overrides):
        defaults = dict(
            project_id=PROJECT_ID,
            project_name="Shop Front",
            story_id=STORY_ID,
            story_key="SHOP-42",
            story_title="Add checkout button",
            previous_assignee_id=ASSIGNEE_ID,
            previous_assignee_email="bob@example.com",
            previous_assignee_name="Bob Ops",
            actor_id=ACTOR_ID,
            actor_name="Jane Dev",
        )
        return build_story_unassigned_payload(**{**defaults, **overrides})

    def test_exact_keys(self):
        payload = self._build()
        expected_keys = {
            "project_id",
            "project_name",
            "story_id",
            "story_key",
            "story_title",
            "previous_assignee_id",
            "previous_assignee_email",
            "previous_assignee_name",
            "actor_id",
            "actor_name",
        }
        assert set(payload.keys()) == expected_keys

    def test_uuids_are_strings(self):
        payload = self._build()
        for key in ("project_id", "story_id", "previous_assignee_id", "actor_id"):
            assert isinstance(payload[key], str)

    def test_values(self):
        payload = self._build()
        assert payload["previous_assignee_email"] == "bob@example.com"
        assert payload["previous_assignee_name"] == "Bob Ops"
        assert payload["project_name"] == "Shop Front"


# ── comment.created ───────────────────────────────────────────────────────────


class TestBuildCommentCreatedPayload:
    def _build(self, **overrides):
        defaults = dict(
            project_id=PROJECT_ID,
            project_name="Shop Front",
            story_id=STORY_ID,
            story_key="SHOP-42",
            story_title="Add checkout button",
            comment_id=COMMENT_ID,
            comment_author_id=ACTOR_ID,
            comment_author_name="Jane Dev",
            reporter_id=REPORTER_ID,
            reporter_email="alice@example.com",
            reporter_name="Alice PM",
            assignee_id=ASSIGNEE_ID,
            assignee_email="bob@example.com",
            assignee_name="Bob Ops",
            body_excerpt="This is a comment",
        )
        return build_comment_created_payload(**{**defaults, **overrides})

    def test_exact_keys(self):
        payload = self._build()
        expected_keys = {
            "project_id",
            "project_name",
            "story_id",
            "story_key",
            "story_title",
            "comment_id",
            "comment_author_id",
            "comment_author_name",
            "comment_body_excerpt",
            "reporter_id",
            "reporter_email",
            "reporter_name",
            "assignee_id",
            "assignee_email",
            "assignee_name",
        }
        assert set(payload.keys()) == expected_keys

    def test_uuids_are_strings(self):
        payload = self._build()
        uuid_keys = (
            "project_id",
            "story_id",
            "comment_id",
            "comment_author_id",
            "reporter_id",
            "assignee_id",
        )
        for key in uuid_keys:
            assert isinstance(payload[key], str)

    def test_body_excerpt_capped_at_200(self):
        long_body = "x" * 300
        payload = self._build(body_excerpt=long_body)
        assert len(payload["comment_body_excerpt"]) == 200

    def test_body_excerpt_short_not_truncated(self):
        payload = self._build(body_excerpt="Short body")
        assert payload["comment_body_excerpt"] == "Short body"

    def test_assignee_none_produces_null_fields(self):
        payload = self._build(assignee_id=None, assignee_email=None, assignee_name=None)
        assert payload["assignee_id"] is None
        assert payload["assignee_email"] is None
        assert payload["assignee_name"] is None

    def test_assignee_present(self):
        payload = self._build()
        assert payload["assignee_id"] == str(ASSIGNEE_ID)
        assert payload["assignee_email"] == "bob@example.com"
        assert payload["assignee_name"] == "Bob Ops"

    def test_reporter_fields(self):
        payload = self._build()
        assert payload["reporter_id"] == str(REPORTER_ID)
        assert payload["reporter_email"] == "alice@example.com"
        assert payload["reporter_name"] == "Alice PM"

    def test_author_field_names(self):
        """Ensure the LLD-canonical field names are used (comment_author_*, not author_*)."""
        payload = self._build()
        assert "comment_author_id" in payload
        assert "comment_author_name" in payload
        # Old field names must NOT appear
        assert "author_id" not in payload
        assert "author_name" not in payload

    def test_body_excerpt_key_name(self):
        """Key must be comment_body_excerpt (not body_excerpt)."""
        payload = self._build()
        assert "comment_body_excerpt" in payload
        assert "body_excerpt" not in payload

    def test_body_excerpt_exactly_200_not_truncated(self):
        body = "y" * 200
        payload = self._build(body_excerpt=body)
        assert payload["comment_body_excerpt"] == body
