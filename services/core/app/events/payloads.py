"""
Event payload builders for domain events.

Payloads are SELF-CONTAINED — every field needed to compose the email and
in-app notification is embedded at publish time. The Notification Service
never calls back to Core or Auth. Recipient email/name are taken from the
denormalized ProjectMember columns set at join time.
"""

from __future__ import annotations

import uuid
from typing import Any


def build_member_added_payload(
    *,
    project_id: uuid.UUID,
    project_name: str,
    project_key: str,
    added_user_id: uuid.UUID,
    added_user_email: str,
    added_user_name: str,
    actor_id: uuid.UUID,
    actor_name: str,
) -> dict[str, Any]:
    """Build payload for ``member.added`` event."""
    return {
        "project_id": str(project_id),
        "project_name": project_name,
        "project_key": project_key,
        "added_user_id": str(added_user_id),
        "added_user_email": added_user_email,
        "added_user_name": added_user_name,
        "actor_id": str(actor_id),
        "actor_name": actor_name,
    }


def build_ownership_transferred_payload(
    *,
    project_id: uuid.UUID,
    project_name: str,
    new_owner_id: uuid.UUID,
    new_owner_email: str,
    new_owner_name: str,
    previous_owner_id: uuid.UUID,
    previous_owner_name: str,
    actor_id: uuid.UUID,
) -> dict[str, Any]:
    """Build payload for ``ownership.transferred`` event."""
    return {
        "project_id": str(project_id),
        "project_name": project_name,
        "new_owner_id": str(new_owner_id),
        "new_owner_email": new_owner_email,
        "new_owner_name": new_owner_name,
        "previous_owner_id": str(previous_owner_id),
        "previous_owner_name": previous_owner_name,
        "actor_id": str(actor_id),
    }


def build_story_assigned_payload(
    *,
    project_id: uuid.UUID,
    project_name: str,
    story_id: uuid.UUID,
    story_key: str,
    story_title: str,
    assignee_id: uuid.UUID,
    assignee_email: str,
    assignee_name: str,
    actor_id: uuid.UUID,
    actor_name: str,
) -> dict[str, Any]:
    """Build payload for ``story.assigned`` event."""
    return {
        "project_id": str(project_id),
        "project_name": project_name,
        "story_id": str(story_id),
        "story_key": story_key,
        "story_title": story_title,
        "assignee_id": str(assignee_id),
        "assignee_email": assignee_email,
        "assignee_name": assignee_name,
        "actor_id": str(actor_id),
        "actor_name": actor_name,
    }


def build_story_unassigned_payload(
    *,
    project_id: uuid.UUID,
    project_name: str,
    story_id: uuid.UUID,
    story_key: str,
    story_title: str,
    previous_assignee_id: uuid.UUID,
    previous_assignee_email: str,
    previous_assignee_name: str,
    actor_id: uuid.UUID,
    actor_name: str,
) -> dict[str, Any]:
    """Build payload for ``story.unassigned`` event."""
    return {
        "project_id": str(project_id),
        "project_name": project_name,
        "story_id": str(story_id),
        "story_key": story_key,
        "story_title": story_title,
        "previous_assignee_id": str(previous_assignee_id),
        "previous_assignee_email": previous_assignee_email,
        "previous_assignee_name": previous_assignee_name,
        "actor_id": str(actor_id),
        "actor_name": actor_name,
    }


def build_comment_created_payload(
    *,
    project_id: uuid.UUID,
    project_name: str,
    story_id: uuid.UUID,
    story_key: str,
    story_title: str,
    comment_id: uuid.UUID,
    comment_author_id: uuid.UUID,
    comment_author_name: str,
    reporter_id: uuid.UUID,
    reporter_email: str,
    reporter_name: str,
    assignee_id: uuid.UUID | None,
    assignee_email: str | None,
    assignee_name: str | None,
    body_excerpt: str,
) -> dict[str, Any]:
    """
    Build payload for ``comment.created`` event.

    Recipients determined by consumer: {assignee_id, reporter_id} minus {comment_author_id}.
    ``body_excerpt`` is capped to 200 chars for email preview use.
    """
    return {
        "project_id": str(project_id),
        "project_name": project_name,
        "story_id": str(story_id),
        "story_key": story_key,
        "story_title": story_title,
        "comment_id": str(comment_id),
        "comment_author_id": str(comment_author_id),
        "comment_author_name": comment_author_name,
        "comment_body_excerpt": body_excerpt[:200],
        "reporter_id": str(reporter_id),
        "reporter_email": reporter_email,
        "reporter_name": reporter_name,
        "assignee_id": str(assignee_id) if assignee_id else None,
        "assignee_email": assignee_email,
        "assignee_name": assignee_name,
    }
