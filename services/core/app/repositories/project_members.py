"""
ProjectMember repository — all raw SQLAlchemy queries for project membership.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_member import ProjectMember


async def get(db: AsyncSession, project_id: int, user_id: int) -> ProjectMember | None:
    """Return the membership row for (project_id, user_id), or None."""
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()
