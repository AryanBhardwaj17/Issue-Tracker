"""
Epic repository — raw SQLAlchemy queries for the Epic aggregate.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.epic import Epic
from app.models.story import StoryStatus, UserStory


async def create(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    name: str,
    description: str | None,
    reporter_id: uuid.UUID,
) -> Epic:
    """Insert a new epic row and flush to obtain its id."""
    epic = Epic(
        project_id=project_id,
        name=name,
        description=description,
        reporter_id=reporter_id,
    )
    db.add(epic)
    await db.flush()
    await db.refresh(epic)
    return epic


async def get_by_id(db: AsyncSession, epic_id: uuid.UUID) -> Epic | None:
    """Return the epic if it exists and is not soft-deleted, else None."""
    result = await db.execute(
        select(Epic).where(Epic.id == epic_id, Epic.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


@dataclass
class EpicRow:
    """Flat projection returned by list queries (epic + pre-computed progress)."""

    epic: Epic
    total: int
    done: int


async def list_with_progress(
    db: AsyncSession,
    project_id: uuid.UUID,
    offset: int,
    limit: int,
) -> list[EpicRow]:
    """
    Return non-deleted epics for a project, each with story progress counts.

    Progress excludes soft-deleted stories on both sides of the fraction.
    A single LEFT JOIN + GROUP BY avoids N+1 queries.
    """
    total_expr = func.count(
        case((UserStory.is_deleted.is_(False), UserStory.id), else_=None)
    )
    done_expr = func.count(
        case(
            (
                (UserStory.is_deleted.is_(False)) & (UserStory.status == StoryStatus.DONE),
                UserStory.id,
            ),
            else_=None,
        )
    )

    stmt = (
        select(Epic, total_expr.label("total"), done_expr.label("done"))
        .outerjoin(UserStory, (UserStory.epic_id == Epic.id))
        .where(Epic.project_id == project_id, Epic.is_deleted.is_(False))
        .group_by(Epic.id)
        .order_by(Epic.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [EpicRow(epic=r.Epic, total=r.total, done=r.done) for r in rows]


async def count_for_project(db: AsyncSession, project_id: uuid.UUID) -> int:
    """Return total number of non-deleted epics in a project."""
    result = await db.execute(
        select(func.count())
        .select_from(Epic)
        .where(Epic.project_id == project_id, Epic.is_deleted.is_(False))
    )
    return result.scalar_one()


async def get_with_progress(
    db: AsyncSession, epic_id: uuid.UUID, project_id: uuid.UUID
) -> EpicRow | None:
    """
    Return a single non-deleted epic with its story progress counts.

    Returns None if the epic does not exist, is soft-deleted, or belongs
    to a different project (prevents cross-project access).
    """
    total_expr = func.count(
        case((UserStory.is_deleted.is_(False), UserStory.id), else_=None)
    )
    done_expr = func.count(
        case(
            (
                (UserStory.is_deleted.is_(False)) & (UserStory.status == StoryStatus.DONE),
                UserStory.id,
            ),
            else_=None,
        )
    )

    stmt = (
        select(Epic, total_expr.label("total"), done_expr.label("done"))
        .outerjoin(UserStory, (UserStory.epic_id == Epic.id))
        .where(
            Epic.id == epic_id,
            Epic.project_id == project_id,
            Epic.is_deleted.is_(False),
        )
        .group_by(Epic.id)
    )
    row = (await db.execute(stmt)).one_or_none()
    if row is None:
        return None
    return EpicRow(epic=row.Epic, total=row.total, done=row.done)
