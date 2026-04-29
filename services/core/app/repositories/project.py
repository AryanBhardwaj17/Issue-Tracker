"""
Project repository — all raw SQLAlchemy queries for the Project aggregate.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


async def get_by_id(db: AsyncSession, project_id: int) -> Project | None:
    """Return the project if it exists and is not soft-deleted, else None."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()
