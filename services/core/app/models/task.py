"""
Task ORM model (unified tasks + subtasks).

A single table handles both tasks (parent_id IS NULL) and subtasks
(parent_id IS NOT NULL).  The 2-level nesting limit is enforced in the service
layer — a row with parent_id set cannot itself be a parent.
`story_id` is always populated, even for subtasks, to simplify queries.
"""

from datetime import UTC, datetime
from datetime import date as DateType

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.story import Priority


class Task(Base):
    """Persisted task / subtask record."""

    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_story_deleted", "story_id", "is_deleted"),
        Index("ix_tasks_parent", "parent_id"),
        Index("ix_tasks_assignee", "assignee_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    story_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_stories.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    assignee_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reporter_id: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[DateType | None] = mapped_column(Date, nullable=True)
    is_done: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
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
    user_story: Mapped["UserStory"] = relationship(back_populates="tasks")  # noqa: F821
    subtasks: Mapped[list["Task"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    parent: Mapped["Task | None"] = relationship(
        back_populates="subtasks",
        remote_side="Task.id",
        lazy="noload",
    )

    def __repr__(self) -> str:
        kind = "Subtask" if self.parent_id else "Task"
        return f"<{kind} id={self.id} title={self.title!r}>"
