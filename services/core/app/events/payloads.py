"""
Event payload builders for domain events.

These build the dict that gets passed to ``publish_event()``.
No gRPC calls here — the consumer resolves emails in E5-S3.
"""

from __future__ import annotations

import uuid
from typing import Any


def build_story_assigned_payload(
    *,
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    story_key: str,
    story_title: str,
    assignee_id: uuid.UUID,
    actor_id: uuid.UUID,
    actor_name: str,
) -> dict[str, Any]:
    """Build payload for ``story.assigned`` event."""
    return {
        "project_id": str(project_id),
        "story_id": str(story_id),
        "story_key": story_key,
        "story_title": story_title,
        "assignee_id": str(assignee_id),
        "actor_id": str(actor_id),
        "actor_name": actor_name,
    }


def build_story_unassigned_payload(
    *,
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    story_key: str,
    story_title: str,
    previous_assignee_id: uuid.UUID,
    actor_id: uuid.UUID,
    actor_name: str,
) -> dict[str, Any]:
    """Build payload for ``story.unassigned`` event."""
    return {
        "project_id": str(project_id),
        "story_id": str(story_id),
        "story_key": story_key,
        "story_title": story_title,
        "previous_assignee_id": str(previous_assignee_id),
        "actor_id": str(actor_id),
        "actor_name": actor_name,
    }
