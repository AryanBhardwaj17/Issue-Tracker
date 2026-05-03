"""
ProjectMember repository — all raw SQLAlchemy queries for project membership.
"""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_member import MemberRole, ProjectMember


async def get(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> ProjectMember | None:
    """Return the membership row for (project_id, user_id), or None."""
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def add_member(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    email: str = "",
    role: MemberRole = MemberRole.MEMBER,
) -> ProjectMember:
    """Insert a new membership row and flush."""
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        name=name,
        email=email,
        role=role,
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


async def list_members(db: AsyncSession, project_id: uuid.UUID) -> list[ProjectMember]:
    """Return all members of a project, ordered by joined_at."""
    result = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.joined_at)
    )
    return list(result.scalars().all())


async def count_members(db: AsyncSession, project_id: uuid.UUID) -> int:
    """Return the total number of members in a project."""
    result = await db.execute(select(func.count()).where(ProjectMember.project_id == project_id))
    return result.scalar_one()


async def update_role(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MemberRole,
) -> None:
    """Update a member's role."""
    await db.execute(
        update(ProjectMember)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .values(role=role.value)
    )
