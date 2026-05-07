"""
Pydantic schemas for the Comment resource.
"""

import uuid
from datetime import datetime

from pydantic import field_validator

from app.schemas.common import CamelModel
from app.utils.constants import COMMENT_BODY_MAX_LENGTH, COMMENT_BODY_MIN_LENGTH


class AuthorRef(CamelModel):
    """Minimal author info embedded in comment responses."""

    id: uuid.UUID
    name: str


class CommentCreate(CamelModel):
    """Request body for POST /stories/:storyId/comments."""

    body: str
    image_url: str | None = None

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < COMMENT_BODY_MIN_LENGTH:
            raise ValueError("Comment body cannot be empty")
        if len(v) > COMMENT_BODY_MAX_LENGTH:
            raise ValueError(f"Comment body cannot exceed {COMMENT_BODY_MAX_LENGTH} characters")
        return v


class CommentUpdate(CamelModel):
    """
    Request body for PATCH /stories/:storyId/comments/:commentId.

    - ``body``: if provided, replaces the current text.
    - ``image_url``: if provided, replaces the current image (triggers old file cleanup).
    - ``remove_image``: if true, clears the image field and deletes the old file.

    ``image_url`` and ``remove_image=true`` are mutually exclusive — do not send both.
    """

    body: str | None = None
    image_url: str | None = None
    remove_image: bool = False

    @field_validator("body")
    @classmethod
    def body_not_empty_if_provided(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) < COMMENT_BODY_MIN_LENGTH:
                raise ValueError("Comment body cannot be empty")
            if len(v) > COMMENT_BODY_MAX_LENGTH:
                raise ValueError(f"Comment body cannot exceed {COMMENT_BODY_MAX_LENGTH} characters")
        return v


class CommentOut(CamelModel):
    """Response shape for a single comment."""

    id: uuid.UUID
    user_story_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    epic_id: uuid.UUID | None = None
    author: AuthorRef
    body: str
    image_url: str | None
    created_at: datetime
    updated_at: datetime
