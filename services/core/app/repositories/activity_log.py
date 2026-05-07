"""
ActivityLog repository — raw SQLAlchemy queries.

All functions flush but do NOT commit — the service layer owns transaction
boundaries. Activity logs are append-only; no update or delete operations.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityAction, ActivityEntityType, ActivityLog


async def create(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    entity_type: ActivityEntityType,
    action: ActivityAction,
    actor_id: uuid.UUID,
    actor_name: str,
    story_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    epic_id: uuid.UUID | None = None,
    field_name: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> ActivityLog:
    """Insert a new activity log entry and flush (does NOT commit)."""
    log = ActivityLog(
        project_id=project_id,
        entity_type=entity_type,
        action=action,
        actor_id=actor_id,
        actor_name=actor_name,
        story_id=story_id,
        task_id=task_id,
        epic_id=epic_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(log)
    await db.flush()
    return log


async def list_for_story(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    page: int,
    page_size: int,
) -> tuple[list[ActivityLog], int]:
    """Return activity logs for a story, ordered newest-first."""
    base = select(ActivityLog).where(ActivityLog.story_id == story_id)
    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = total_result.scalar_one()

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base.order_by(ActivityLog.created_at.desc()).offset(offset).limit(page_size)
    )
    return list(rows_result.scalars().all()), total


async def list_for_task(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    page: int,
    page_size: int,
) -> tuple[list[ActivityLog], int]:
    """Return activity logs for a task (or subtask), ordered newest-first."""
    base = select(ActivityLog).where(ActivityLog.task_id == task_id)
    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = total_result.scalar_one()

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base.order_by(ActivityLog.created_at.desc()).offset(offset).limit(page_size)
    )
    return list(rows_result.scalars().all()), total


async def list_for_epic(
    db: AsyncSession,
    *,
    epic_id: uuid.UUID,
    page: int,
    page_size: int,
) -> tuple[list[ActivityLog], int]:
    """Return activity logs for an epic, ordered newest-first."""
    base = select(ActivityLog).where(ActivityLog.epic_id == epic_id)
    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = total_result.scalar_one()

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base.order_by(ActivityLog.created_at.desc()).offset(offset).limit(page_size)
    )
    return list(rows_result.scalars().all()), total


async def list_for_project(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    page: int,
    page_size: int,
) -> tuple[list[ActivityLog], int]:
    """Return all activity logs for a project, ordered newest-first."""
    base = select(ActivityLog).where(ActivityLog.project_id == project_id)
    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = total_result.scalar_one()

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base.order_by(ActivityLog.created_at.desc()).offset(offset).limit(page_size)
    )
    return list(rows_result.scalars().all()), total
