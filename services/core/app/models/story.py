"""
UserStory ORM model.

Core work-item. `story_key` is a globally unique slug (e.g. SHOP-42) stored
directly on the row.  No sprint_id is present in this v2 schema.
Fibonacci-only story_points validation is enforced at the service layer.
"""

import enum
import uuid
from datetime import UTC, datetime
from datetime import date as DateType

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StoryStatus(enum.StrEnum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    TESTING = "testing"
    READY_FOR_PROD = "ready_for_prod"
    DONE = "done"


class Priority(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UserStory(Base):
    """Persisted user story record."""

    __tablename__ = "user_stories"
    __table_args__ = (
        UniqueConstraint("project_id", "story_key", name="uq_user_stories_project_key"),
        CheckConstraint(
            "story_points IN (1,2,3,5,8,13,21)",
            name="ck_user_stories_fibonacci_points",
        ),
        Index("ix_user_stories_project_status_deleted", "project_id", "status", "is_deleted"),
        Index("ix_user_stories_assignee", "assignee_id"),
        Index("ix_user_stories_epic", "epic_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    story_key: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    epic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("epics.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[StoryStatus] = mapped_column(
        Enum(StoryStatus, name="story_status", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StoryStatus.BACKLOG,
        server_default="backlog",
    )
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    story_points: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reporter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    due_date: Mapped[DateType | None] = mapped_column(Date, nullable=True)
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
    project: Mapped["Project"] = relationship(back_populates="stories")  # noqa: F821
    epic: Mapped["Epic | None"] = relationship(back_populates="stories")  # noqa: F821
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        back_populates="user_story",
        lazy="noload",
    )
    comments: Mapped[list["Comment"]] = relationship(  # noqa: F821
        back_populates="user_story",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<UserStory id={self.id} key={self.story_key!r} status={self.status}>"
