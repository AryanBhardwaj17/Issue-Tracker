"""
Pydantic schemas for Project and ProjectMember request/response DTOs.

All response schemas use camelCase on the wire (via ``CamelModel``).
Request schemas accept both camelCase (from clients) and snake_case internally.
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import CamelModel
from app.utils.constants import (
    PROJECT_DESCRIPTION_MAX_LENGTH,
    PROJECT_NAME_MAX_LENGTH,
    PROJECT_NAME_MIN_LENGTH,
)

# ── Request schemas ───────────────────────────────────────────────────────────


class ProjectCreateRequest(CamelModel):
    """Body for POST /api/v1/projects."""

    name: str = Field(..., min_length=PROJECT_NAME_MIN_LENGTH, max_length=PROJECT_NAME_MAX_LENGTH)
    description: str | None = Field(None, max_length=PROJECT_DESCRIPTION_MAX_LENGTH)

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("name")
    @classmethod
    def _must_contain_letter(cls, v: str) -> str:
        import re

        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Project name must contain at least one letter")
        return v


class ProjectUpdateRequest(CamelModel):
    """Body for PATCH /api/v1/projects/:id — all fields optional."""

    name: str | None = Field(
        None, min_length=PROJECT_NAME_MIN_LENGTH, max_length=PROJECT_NAME_MAX_LENGTH
    )
    description: str | None = Field(None, max_length=PROJECT_DESCRIPTION_MAX_LENGTH)

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v

    @field_validator("name")
    @classmethod
    def _must_contain_letter(cls, v: str | None) -> str | None:
        import re

        if v is not None and not re.search(r"[A-Za-z]", v):
            raise ValueError("Project name must contain at least one letter")
        return v


# ── Response schemas ──────────────────────────────────────────────────────────


class OwnerOut(CamelModel):
    """Minimal owner info embedded in project responses."""

    id: UUID
    name: str


class ProjectOut(CamelModel):
    """Full project detail — used for create/get/update responses."""

    id: UUID
    name: str
    key: str
    description: str | None
    owner: OwnerOut
    role: str  # caller's role in this project
    member_count: int
    created_at: datetime
    updated_at: datetime


class ProjectListItem(CamelModel):
    """Condensed project row returned in list responses."""

    id: UUID
    name: str
    key: str
    description: str | None
    role: str
    member_count: int
    created_at: datetime
    updated_at: datetime
