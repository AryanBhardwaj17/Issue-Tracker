"""
Pydantic schemas for Epic request/response DTOs.
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import CamelModel

# ── Request schemas ───────────────────────────────────────────────────────────


class EpicCreate(CamelModel):
    """Body for POST /api/v1/projects/{project_id}/epics."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=10_000)


class EpicUpdate(CamelModel):
    """Body for PATCH /api/v1/projects/{project_id}/epics/{epic_id} — all fields optional."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=10_000)


# ── Response schemas ──────────────────────────────────────────────────────────


class ReporterRef(CamelModel):
    """Minimal reporter info embedded in epic responses."""

    id: UUID
    name: str


class EpicProgressOut(CamelModel):
    """Stories progress: how many total and how many done (excludes soft-deleted stories)."""

    total: int
    done: int


class EpicOut(CamelModel):
    """Full epic record returned by create / get / update."""

    id: UUID
    name: str
    description: str | None
    reporter: ReporterRef
    progress: EpicProgressOut
    created_at: datetime
    updated_at: datetime
