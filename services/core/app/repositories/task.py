"""
Task repository — all raw SQLAlchemy queries for the Task entity.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task


async def create(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    parent_id: uuid.UUID | None = None,
    title: str,
    description: str | None = None,
    priority: str,
    assignee_id: uuid.UUID | None = None,
    reporter_id: uuid.UUID,
    due_date=None,
) -> Task:
    """Insert a new task/subtask row and flush."""
    task = Task(
        project_id=project_id,
        story_id=story_id,
        parent_id=parent_id,
        title=title,
        description=description,
        priority=priority,
        assignee_id=assignee_id,
        reporter_id=reporter_id,
        due_date=due_date,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def get_by_id(db: AsyncSession, task_id: uuid.UUID) -> Task | None:
    """Return a task if it exists and is not soft-deleted, else None."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def list_for_story(
    db: AsyncSession,
    story_id: uuid.UUID,
) -> list[Task]:
    """
    Return all non-deleted tasks and subtasks for a story,
    ordered so parents come before their subtasks.
    """
    result = await db.execute(
        select(Task)
        .where(Task.story_id == story_id, Task.is_deleted.is_(False))
        .order_by(Task.parent_id.is_(None).desc(), Task.parent_id, Task.created_at)
    )
    return list(result.scalars().all())


async def count_top_level_for_story(db: AsyncSession, story_id: uuid.UUID) -> int:
    """Count non-deleted top-level tasks (parent_id IS NULL) for a story."""
    result = await db.execute(
        select(func.count()).where(
            Task.story_id == story_id,
            Task.parent_id.is_(None),
            Task.is_deleted.is_(False),
        )
    )
    return result.scalar_one()


async def list_top_level_for_story(
    db: AsyncSession,
    story_id: uuid.UUID,
    offset: int,
    limit: int,
) -> list[Task]:
    """Return paginated top-level tasks (parent_id IS NULL) for a story."""
    result = await db.execute(
        select(Task)
        .where(
            Task.story_id == story_id,
            Task.parent_id.is_(None),
            Task.is_deleted.is_(False),
        )
        .order_by(Task.created_at)
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_subtasks(db: AsyncSession, parent_id: uuid.UUID) -> list[Task]:
    """Return all non-deleted subtasks of a given parent task."""
    result = await db.execute(
        select(Task)
        .where(Task.parent_id == parent_id, Task.is_deleted.is_(False))
        .order_by(Task.created_at)
    )
    return list(result.scalars().all())


async def count_subtasks(db: AsyncSession, parent_id: uuid.UUID) -> int:
    """Count non-deleted subtasks of a given parent task."""
    result = await db.execute(
        select(func.count()).where(
            Task.parent_id == parent_id,
            Task.is_deleted.is_(False),
        )
    )
    return result.scalar_one()


async def update_fields(
    db: AsyncSession,
    task_id: uuid.UUID,
    **values,
) -> None:
    """Partial update of mutable task fields."""
    values["updated_at"] = datetime.now(UTC)
    await db.execute(update(Task).where(Task.id == task_id).values(**values))


async def soft_delete(db: AsyncSession, task_id: uuid.UUID) -> None:
    """Set is_deleted=True on a single task row."""
    await db.execute(
        update(Task).where(Task.id == task_id).values(is_deleted=True, updated_at=datetime.now(UTC))
    )


async def soft_delete_subtasks(db: AsyncSession, parent_id: uuid.UUID) -> None:
    """Soft-delete all subtasks of a given parent task."""
    await db.execute(
        update(Task)
        .where(Task.parent_id == parent_id, Task.is_deleted.is_(False))
        .values(is_deleted=True, updated_at=datetime.now(UTC))
    )


async def soft_delete_by_story(db: AsyncSession, story_id: uuid.UUID) -> None:
    """Soft-delete all tasks and subtasks belonging to a story."""
    await db.execute(
        update(Task)
        .where(Task.story_id == story_id, Task.is_deleted.is_(False))
        .values(is_deleted=True, updated_at=datetime.now(UTC))
    )
