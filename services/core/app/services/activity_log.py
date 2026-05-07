"""
ActivityLog service — business logic for reading activity feeds and logging mutations.

Read functions validate entity ownership and paginate.
The ``log_activity`` helper is called from story/task/epic services after mutations.
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ProjectMembership
from app.core.exceptions import EpicNotFoundError, StoryNotFoundError, TaskNotFoundError
from app.models.activity_log import ActivityAction, ActivityEntityType
from app.repositories import activity_log as activity_repo
from app.repositories import epic as epic_repo
from app.repositories import story as story_repo
from app.repositories import task as task_repo
from app.schemas.activity_log import ActivityLogOut
from app.schemas.common import Pagination, paginate

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _to_out(log) -> ActivityLogOut:
    """Convert an ActivityLog ORM row to the response DTO."""
    return ActivityLogOut(
        id=log.id,
        project_id=log.project_id,
        story_id=log.story_id,
        task_id=log.task_id,
        epic_id=log.epic_id,
        entity_type=log.entity_type.value if hasattr(log.entity_type, "value") else log.entity_type,
        action=log.action.value if hasattr(log.action, "value") else log.action,
        field_name=log.field_name,
        old_value=log.old_value,
        new_value=log.new_value,
        actor_id=log.actor_id,
        actor_name=log.actor_name,
        created_at=log.created_at,
    )


# ── Write helper (called from other services) ────────────────────────────────


async def log_activity(
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
) -> None:
    """
    Write a single activity log entry. Never raises — failures are logged as warnings.

    This function flushes but does NOT commit. The caller owns the transaction.
    """
    try:
        await activity_repo.create(
            db,
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
    except Exception:
        logger.warning(
            "Failed to write activity log: entity_type=%s action=%s actor=%s",
            entity_type,
            action,
            actor_id,
            exc_info=True,
        )


# ── Read functions ────────────────────────────────────────────────────────────


async def get_story_activity(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    membership: ProjectMembership,
    page: int,
    page_size: int,
) -> tuple[list[ActivityLogOut], Pagination]:
    """Return paginated activity for a story. Raises StoryNotFoundError if absent."""
    story = await story_repo.get_active(db, story_id, membership.project_id)
    if story is None:
        raise StoryNotFoundError()

    rows, total = await activity_repo.list_for_story(
        db, story_id=story_id, page=page, page_size=page_size
    )
    items = [_to_out(r) for r in rows]
    return items, paginate(page, page_size, total)


async def get_task_activity(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    membership: ProjectMembership,
    page: int,
    page_size: int,
) -> tuple[list[ActivityLogOut], Pagination]:
    """Return paginated activity for a task/subtask. Raises TaskNotFoundError if absent."""
    task = await task_repo.get_by_id(db, task_id)
    if task is None or task.project_id != membership.project_id:
        raise TaskNotFoundError()

    rows, total = await activity_repo.list_for_task(
        db, task_id=task_id, page=page, page_size=page_size
    )
    items = [_to_out(r) for r in rows]
    return items, paginate(page, page_size, total)


async def get_epic_activity(
    db: AsyncSession,
    *,
    epic_id: uuid.UUID,
    membership: ProjectMembership,
    page: int,
    page_size: int,
) -> tuple[list[ActivityLogOut], Pagination]:
    """Return paginated activity for an epic. Raises EpicNotFoundError if absent."""
    epic = await epic_repo.get_by_id(db, epic_id)
    if epic is None or epic.project_id != membership.project_id or epic.is_deleted:
        raise EpicNotFoundError()

    rows, total = await activity_repo.list_for_epic(
        db, epic_id=epic_id, page=page, page_size=page_size
    )
    items = [_to_out(r) for r in rows]
    return items, paginate(page, page_size, total)


async def get_project_activity(
    db: AsyncSession,
    *,
    membership: ProjectMembership,
    page: int,
    page_size: int,
) -> tuple[list[ActivityLogOut], Pagination]:
    """Return paginated activity for the entire project."""
    rows, total = await activity_repo.list_for_project(
        db, project_id=membership.project_id, page=page, page_size=page_size
    )
    items = [_to_out(r) for r in rows]
    return items, paginate(page, page_size, total)
