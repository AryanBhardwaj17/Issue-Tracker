"""Test payload factory helpers — shared across all test modules."""

import uuid


def make_member_added_payload(**overrides) -> dict:
    defaults = {
        "project_id": str(uuid.uuid4()),
        "project_name": "Test Project",
        "project_key": "TP",
        "added_user_id": str(uuid.uuid4()),
        "added_user_email": "bob@test.com",
        "added_user_name": "Bob",
        "actor_id": str(uuid.uuid4()),
        "actor_name": "Alice",
    }
    defaults.update(overrides)
    return defaults


def make_ownership_transferred_payload(**overrides) -> dict:
    defaults = {
        "project_id": str(uuid.uuid4()),
        "project_name": "Test Project",
        "new_owner_id": str(uuid.uuid4()),
        "new_owner_email": "charlie@test.com",
        "new_owner_name": "Charlie",
        "previous_owner_id": str(uuid.uuid4()),
        "previous_owner_name": "Alice",
        "actor_id": str(uuid.uuid4()),
    }
    defaults.update(overrides)
    return defaults


def make_story_assigned_payload(**overrides) -> dict:
    defaults = {
        "project_id": str(uuid.uuid4()),
        "project_name": "Test Project",
        "story_id": str(uuid.uuid4()),
        "story_key": "TP-42",
        "story_title": "Fix login bug",
        "assignee_id": str(uuid.uuid4()),
        "assignee_email": "bob@test.com",
        "assignee_name": "Bob",
        "actor_id": str(uuid.uuid4()),
        "actor_name": "Alice",
    }
    defaults.update(overrides)
    return defaults


def make_story_unassigned_payload(**overrides) -> dict:
    defaults = {
        "project_id": str(uuid.uuid4()),
        "project_name": "Test Project",
        "story_id": str(uuid.uuid4()),
        "story_key": "TP-42",
        "story_title": "Fix login bug",
        "previous_assignee_id": str(uuid.uuid4()),
        "previous_assignee_email": "bob@test.com",
        "previous_assignee_name": "Bob",
        "actor_id": str(uuid.uuid4()),
        "actor_name": "Alice",
    }
    defaults.update(overrides)
    return defaults


def make_comment_created_payload(**overrides) -> dict:
    defaults = {
        "project_id": str(uuid.uuid4()),
        "project_name": "Test Project",
        "story_id": str(uuid.uuid4()),
        "story_key": "TP-42",
        "story_title": "Fix login bug",
        "comment_id": str(uuid.uuid4()),
        "comment_author_id": str(uuid.uuid4()),
        "comment_author_name": "Eve",
        "comment_body_excerpt": "Looks good to me!",
        "reporter_id": str(uuid.uuid4()),
        "reporter_email": "bob@test.com",
        "reporter_name": "Bob",
        "assignee_id": str(uuid.uuid4()),
        "assignee_email": "charlie@test.com",
        "assignee_name": "Charlie",
    }
    defaults.update(overrides)
    return defaults
