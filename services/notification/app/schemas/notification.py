"""Pydantic response schemas for the Notification API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    """Single notification item returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    title: str
    body: str
    link: str | None
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Envelope for paginated notification list."""

    success: bool = True
    message: str = "ok"
    data: list[NotificationOut]
    pagination: dict


class UnreadCountResponse(BaseModel):
    """Envelope for unread count."""

    success: bool = True
    message: str = "ok"
    data: dict


class MarkReadResponse(BaseModel):
    """Envelope after marking notification(s) as read."""

    success: bool = True
    message: str = "ok"
    data: NotificationOut | None = None
