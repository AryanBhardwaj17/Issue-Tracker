"""
Pydantic schemas for ActivityLog responses.

Activity logs are append-only — no create/update schema needed from the API
perspective. Logs are written internally by service hooks.
"""

import uuid
from datetime import datetime

from app.schemas.common import CamelModel


class ActivityLogOut(CamelModel):
    """Response shape for a single activity log entry."""

    id: uuid.UUID
    project_id: uuid.UUID
    story_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    epic_id: uuid.UUID | None = None
    entity_type: str
    action: str
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    actor_id: uuid.UUID
    actor_name: str
    created_at: datetime
