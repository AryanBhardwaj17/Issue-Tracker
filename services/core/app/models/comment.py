"""
Comment ORM model.

Belongs to a user story. Supports an optional image attachment stored as a
relative path under /uploads/. Soft-deleted via is_deleted flag.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Comment(Base):
    """Persisted comment record."""

    __tablename__ = "comments"
    __table_args__ = (Index("ix_comments_user_story_deleted", "user_story_id", "is_deleted"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_stories.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    body: Mapped[str] = mapped_column(String, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    user_story: Mapped["UserStory"] = relationship(back_populates="comments")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Comment id={self.id} user_story_id={self.user_story_id}>"
