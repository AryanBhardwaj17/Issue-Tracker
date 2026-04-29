"""
ProjectMember repository — all raw SQLAlchemy queries for project membership.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_member import ProjectMember


async def get(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> ProjectMember | None:
    """Return the membership row for (project_id, user_id), or None."""
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()
