"""
Pydantic schemas for task/subtask request/response DTOs.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.models.story import Priority
from app.schemas.common import CamelModel
from app.utils.constants import TASK_TITLE_MAX_LENGTH

# ── Request schemas ───────────────────────────────────────────────────────────


class TaskCreateRequest(CamelModel):
    """Body for POST .../tasks or .../subtasks."""

    title: str = Field(..., min_length=1, max_length=TASK_TITLE_MAX_LENGTH)
    description: str | None = Field(None)
    priority: Priority = Field(...)
    assignee_id: UUID | None = Field(None)
    due_date: date | None = Field(None)


class TaskUpdateRequest(CamelModel):
    """Body for PATCH .../tasks/{task_id} or .../subtasks/{subtask_id}."""

    title: str | None = Field(None, min_length=1, max_length=TASK_TITLE_MAX_LENGTH)
    description: str | None = Field(None)
    priority: Priority | None = Field(None)
    assignee_id: UUID | None = Field(None)
    due_date: date | None = Field(None)
    is_done: bool | None = Field(None)


# ── Response schemas ──────────────────────────────────────────────────────────


class AssigneeOut(CamelModel):
    """Lightweight assignee reference resolved from project_members."""

    id: UUID
    name: str


class SubtaskOut(CamelModel):
    """Flat subtask record (no further nesting)."""

    id: UUID
    parent_id: UUID
    title: str
    description: str | None
    priority: str
    assignee: AssigneeOut | None
    reporter_id: UUID
    due_date: date | None
    is_done: bool
    created_at: datetime
    updated_at: datetime


class TaskOut(CamelModel):
    """Top-level task with nested subtasks."""

    id: UUID
    story_id: UUID
    parent_id: UUID | None = None
    title: str
    description: str | None
    priority: str
    assignee: AssigneeOut | None
    reporter_id: UUID
    due_date: date | None
    is_done: bool
    created_at: datetime
    updated_at: datetime
    subtasks: list[SubtaskOut] = Field(default_factory=list)
