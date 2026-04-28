"""
Pydantic schemas for user read/update operations.

``UserResponse`` is used as the public representation of a user — it is
returned by the API and never exposes the password hash.
``UserUpdate`` carries optional fields for profile edits; only non-None
fields are applied by the service layer.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    """Public user representation returned by API responses."""

    id: uuid.UUID
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
