"""
ActivityLog ORM model.

Append-only audit log of every mutation event across stories, tasks, subtasks,
and epics — consumed by the story timeline, task timeline, and project feed.

No updated_at, no is_deleted — activity is immutable by design.
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ActivityEntityType(enum.StrEnum):
    """Discriminator for which entity produced this activity entry."""

    story = "story"
    task = "task"
    subtask = "subtask"
    epic = "epic"


class ActivityAction(enum.StrEnum):
    """The type of mutation that occurred."""

    created = "created"
    deleted = "deleted"
    restored = "restored"
    status_changed = "status_changed"
    assigned = "assigned"
    completed = "completed"
    field_updated = "field_updated"


class ActivityLog(Base):
    """Persisted activity log entry — append-only, never updated or soft-deleted."""

    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_project_created", "project_id", "created_at"),
        Index("ix_activity_story_created", "story_id", "created_at"),
        Index("ix_activity_task_created", "task_id", "created_at"),
        Index("ix_activity_epic_created", "epic_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    story_id: Mapped[uuid.UUID | None] = mapped_column(
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
    entity_type: Mapped[ActivityEntityType] = mapped_column(
        SAEnum(ActivityEntityType, name="activity_entity_type", create_type=False),
        nullable=False,
    )
    action: Mapped[ActivityAction] = mapped_column(
        SAEnum(ActivityAction, name="activity_action", create_type=False),
        nullable=False,
    )
    field_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    old_value: Mapped[str | None] = mapped_column(String, nullable=True)
    new_value: Mapped[str | None] = mapped_column(String, nullable=True)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return (
            f"<ActivityLog id={self.id} entity_type={self.entity_type} "
            f"action={self.action} actor={self.actor_name}>"
        )
