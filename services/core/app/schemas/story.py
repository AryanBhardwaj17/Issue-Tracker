"""
Pydantic schemas for UserStory request/response DTOs.
"""

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import CamelModel
from app.utils.constants import (
    FIBONACCI_POINTS,
    STORY_DESCRIPTION_MAX_LENGTH,
    STORY_TITLE_MAX_LENGTH,
    STORY_TITLE_MIN_LENGTH,
)

# ── Request schemas ───────────────────────────────────────────────────────────


class StoryCreate(CamelModel):
    """Body for POST /api/v1/projects/{project_id}/stories."""

    title: str = Field(..., min_length=STORY_TITLE_MIN_LENGTH, max_length=STORY_TITLE_MAX_LENGTH)
    description: str | None = Field(None, max_length=STORY_DESCRIPTION_MAX_LENGTH)
    epic_id: UUID | None = None
    status: str | None = Field(None, description="Only 'backlog' or 'todo' allowed")
    priority: str
    story_points: int | None = None
    assignee_id: UUID | None = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            msg = "Title must not be blank"
            raise ValueError(msg)
        return stripped

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            msg = f"Priority must be one of {', '.join(sorted(allowed))}"
            raise ValueError(msg)
        return v

    @field_validator("story_points")
    @classmethod
    def validate_fibonacci(cls, v: int | None) -> int | None:
        if v is not None and v not in FIBONACCI_POINTS:
            msg = f"Story points must be one of {sorted(FIBONACCI_POINTS)}"
            raise ValueError(msg)
        return v


class StoryPatch(CamelModel):
    """Body for PATCH /api/v1/projects/{project_id}/stories/{story_id} — all fields optional."""

    title: str | None = Field(
        None,
        min_length=STORY_TITLE_MIN_LENGTH,
        max_length=STORY_TITLE_MAX_LENGTH,
    )
    description: str | None = Field(None, max_length=STORY_DESCRIPTION_MAX_LENGTH)
    epic_id: UUID | None = None
    status: str | None = None
    priority: str | None = None
    story_points: Annotated[int | None, Field()] = None
    assignee_id: UUID | None = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                msg = "Title must not be blank"
                raise ValueError(msg)
            return stripped
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"low", "medium", "high", "critical"}
            if v not in allowed:
                msg = f"Priority must be one of {', '.join(sorted(allowed))}"
                raise ValueError(msg)
        return v

    @field_validator("story_points")
    @classmethod
    def validate_fibonacci(cls, v: int | None) -> int | None:
        if v is not None and v not in FIBONACCI_POINTS:
            msg = f"Story points must be one of {sorted(FIBONACCI_POINTS)}"
            raise ValueError(msg)
        return v


# ── Response schemas ──────────────────────────────────────────────────────────


class UserRef(CamelModel):
    """Minimal user reference embedded in story responses."""

    id: UUID
    name: str


class StoryOut(CamelModel):
    """Full story record returned by create / get / update / list."""

    id: UUID
    story_key: str
    title: str
    description: str | None
    epic_id: UUID | None
    status: str
    priority: str
    story_points: int | None
    assignee: UserRef | None
    reporter: UserRef
    due_date: date | None
    created_at: datetime
    updated_at: datetime
