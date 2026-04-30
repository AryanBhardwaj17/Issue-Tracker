"""
Pydantic schemas for member management request/response DTOs.
"""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.common import CamelModel

# ── Request schemas ───────────────────────────────────────────────────────────


class AddMemberRequest(CamelModel):
    """Body for POST /api/v1/projects/{project_id}/members."""

    email: EmailStr = Field(..., description="Email of the user to add")


class TransferOwnershipRequest(CamelModel):
    """Body for POST /api/v1/projects/{project_id}/transfer-ownership."""

    new_owner_id: UUID = Field(..., description="UUID of the new owner")


# ── Response schemas ──────────────────────────────────────────────────────────


class MemberOut(CamelModel):
    """Single member record returned in list and add responses."""

    id: UUID
    user_id: UUID
    name: str
    email: str
    role: str
    joined_at: datetime
