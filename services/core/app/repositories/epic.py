"""
Epic repository — raw SQLAlchemy queries for the Epic aggregate.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.epic import Epic


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
