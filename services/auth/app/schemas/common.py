"""
Shared Pydantic response schemas reused across multiple routes.
"""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Generic success response carrying a human-readable message."""

    message: str
