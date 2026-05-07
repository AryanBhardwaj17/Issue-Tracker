"""
Comment ORM model.

Belongs to exactly one of: user story, task, or epic (enforced by DB CHECK
constraint). Supports an optional image attachment stored as a relative path
under /uploads/. Soft-deleted via is_deleted flag.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Comment(Base):
    """Persisted comment record."""

    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_user_story_deleted", "user_story_id", "is_deleted"),
        Index("ix_comments_task_deleted", "task_id", "is_deleted"),
        Index("ix_comments_epic_deleted", "epic_id", "is_deleted"),
        CheckConstraint(
            "(CASE WHEN user_story_id IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN task_id IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN epic_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_comments_one_owner",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_story_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_stories.id", ondelete="SET NULL"),
        nullable=True,
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    epic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("epics.id", ondelete="SET NULL"),
        nullable=True,
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
    user_story: Mapped["UserStory | None"] = relationship(back_populates="comments")  # noqa: F821
    task: Mapped["Task | None"] = relationship(lazy="noload")  # noqa: F821
    epic: Mapped["Epic | None"] = relationship(lazy="noload")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Comment id={self.id} user_story_id={self.user_story_id}>"
