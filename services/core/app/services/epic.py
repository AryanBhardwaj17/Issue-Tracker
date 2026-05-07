"""
Epic service — business logic for the Epic aggregate.

Responsibilities:
- Create, list, get, update, soft-delete epics.
- Progress computation (total / done non-deleted stories).
- Soft-delete unlinks stories (sets epic_id = NULL) rather than cascading.

All DB I/O is delegated to ``repositories.epic``.
Reporter names are resolved from ``project_members`` (denormalised).
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership
from app.core.exceptions import EpicDeleteForbiddenError, EpicEditForbiddenError, EpicNotFoundError
from app.models.activity_log import ActivityAction, ActivityEntityType
from app.models.project_member import ProjectMember
from app.repositories import epic as epic_repo
from app.repositories import project_members as member_repo
from app.schemas.common import Pagination, paginate
from app.schemas.epic import EpicOut, EpicProgressOut, EpicUpdate, ReporterRef
from app.services.activity_log import log_activity
from app.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _resolve_reporter_name(
    db: AsyncSession, project_id: uuid.UUID, reporter_id: uuid.UUID
) -> str:
    """Look up the reporter's display name from project_members."""
    member = await member_repo.get(db, project_id, reporter_id)
    return member.name if member else ""


def _to_epic_out(epic, reporter_name: str, total: int = 0, done: int = 0) -> EpicOut:
    return EpicOut(
        id=epic.id,
        name=epic.name,
        description=epic.description,
        reporter=ReporterRef(id=epic.reporter_id, name=reporter_name),
        progress=EpicProgressOut(total=total, done=done),
        created_at=epic.created_at,
        updated_at=epic.updated_at,
    )


# ── Service functions ─────────────────────────────────────────────────────────


async def create_epic(
    db: AsyncSession,
    *,
    membership: ProjectMembership,
    user: CurrentUser,
    name: str,
    description: str | None,
) -> EpicOut:
    """Create an epic and return its full representation."""
    epic = await epic_repo.create(
        db,
        project_id=membership.project_id,
        name=name,
        description=description,
        reporter_id=user.id,
    )

    await log_activity(
        db,
        project_id=membership.project_id,
        entity_type=ActivityEntityType.epic,
        action=ActivityAction.created,
        actor_id=user.id,
        actor_name=user.name,
        epic_id=epic.id,
    )

    await db.commit()
    await db.refresh(epic)

    logger.info("Epic created: id=%s project=%s by user=%s", epic.id, epic.project_id, user.id)
    return _to_epic_out(epic, reporter_name=user.name)


async def list_epics(
    db: AsyncSession,
    *,
    membership: ProjectMembership,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[EpicOut], Pagination]:
    """Return paginated epics for a project, each with live progress counts."""
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    total = await epic_repo.count_for_project(db, membership.project_id)
    rows = await epic_repo.list_with_progress(
        db, membership.project_id, offset=offset, limit=page_size
    )

    # Batch-resolve reporter names from project_members (one query).
    reporter_ids = list({r.epic.reporter_id for r in rows})
    name_by_id: dict[uuid.UUID, str] = {}
    if reporter_ids:
        result = await db.execute(
            select(ProjectMember.user_id, ProjectMember.name).where(
                ProjectMember.project_id == membership.project_id,
                ProjectMember.user_id.in_(reporter_ids),
            )
        )
        name_by_id = {row.user_id: row.name for row in result}

    items = [
        _to_epic_out(
            r.epic,
            reporter_name=name_by_id.get(r.epic.reporter_id, ""),
            total=r.total,
            done=r.done,
        )
        for r in rows
    ]
    return items, paginate(page, page_size, total)


async def get_epic(
    db: AsyncSession,
    *,
    epic_id: uuid.UUID,
    membership: ProjectMembership,
) -> EpicOut:
    """Return a single epic with progress. Raises EpicNotFoundError if absent."""
    row = await epic_repo.get_with_progress(db, epic_id, membership.project_id)
    if row is None:
        raise EpicNotFoundError()

    reporter_name = await _resolve_reporter_name(db, membership.project_id, row.epic.reporter_id)
    return _to_epic_out(row.epic, reporter_name=reporter_name, total=row.total, done=row.done)


async def update_epic(
    db: AsyncSession,
    *,
    epic_id: uuid.UUID,
    membership: ProjectMembership,
    user: CurrentUser,
    data: EpicUpdate,
) -> EpicOut:
    """
    Partial update of an epic's name and/or description.

    Only the epic's reporter or a project owner may edit.
    Raises EpicNotFoundError if the epic is absent or belongs to another project.
    Raises EpicEditForbiddenError if the caller is neither the reporter nor the owner.
    """
    row = await epic_repo.get_with_progress(db, epic_id, membership.project_id)
    if row is None:
        raise EpicNotFoundError()

    if row.epic.reporter_id != user.id and membership.role != "owner":
        raise EpicEditForbiddenError()

    # Capture old values for activity logging
    old_name = row.epic.name
    old_description = row.epic.description

    await epic_repo.update_fields(db, epic_id, name=data.name, description=data.description)

    # Log activity per changed field
    if data.name is not None and data.name != old_name:
        await log_activity(
            db,
            project_id=membership.project_id,
            entity_type=ActivityEntityType.epic,
            action=ActivityAction.field_updated,
            actor_id=user.id,
            actor_name=user.name,
            epic_id=epic_id,
            field_name="name",
            old_value=old_name,
            new_value=data.name,
        )
    if data.description is not None and data.description != old_description:
        await log_activity(
            db,
            project_id=membership.project_id,
            entity_type=ActivityEntityType.epic,
            action=ActivityAction.field_updated,
            actor_id=user.id,
            actor_name=user.name,
            epic_id=epic_id,
            field_name="description",
            old_value=old_description,
            new_value=data.description,
        )

    await db.commit()
    await db.refresh(row.epic)

    reporter_name = await _resolve_reporter_name(db, membership.project_id, row.epic.reporter_id)
    return _to_epic_out(row.epic, reporter_name=reporter_name, total=row.total, done=row.done)


async def delete_epic(
    db: AsyncSession,
    *,
    epic_id: uuid.UUID,
    membership: ProjectMembership,
    user: CurrentUser,
) -> None:
    """
    Soft-delete an epic and cascade to its stories, tasks, and subtasks.

    Only the epic's reporter or a project owner may delete.
    Raises EpicNotFoundError if the epic is absent or belongs to another project.
    Raises EpicDeleteForbiddenError if the caller is neither the reporter nor the owner.
    """
    row = await epic_repo.get_with_progress(db, epic_id, membership.project_id)
    if row is None:
        raise EpicNotFoundError()

    if row.epic.reporter_id != user.id and membership.role != "owner":
        raise EpicDeleteForbiddenError()

    await log_activity(
        db,
        project_id=membership.project_id,
        entity_type=ActivityEntityType.epic,
        action=ActivityAction.deleted,
        actor_id=user.id,
        actor_name=user.name,
        epic_id=epic_id,
    )

    await epic_repo.cascade_soft_delete(db, epic_id)
    await db.commit()

    logger.info(
        "Epic deleted: id=%s project=%s by user=%s",
        epic_id,
        membership.project_id,
        user.id,
    )
