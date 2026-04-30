"""
Project repository — all raw SQLAlchemy queries for the Project aggregate.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import MemberRole, ProjectMember


async def get_by_id(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """Return the project if it exists and is not soft-deleted, else None."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def get_by_key(db: AsyncSession, key: str) -> Project | None:
    """
    Return a project by its unique key.

    Includes soft-deleted projects for uniqueness checks.
    """
    result = await db.execute(select(Project).where(Project.key == key))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    name: str,
    key: str,
    description: str | None,
    owner_id: int,
) -> Project:
    """Insert a new project row and flush to obtain its id."""
    project = Project(name=name, key=key, description=description, owner_id=owner_id)
    db.add(project)
    await db.flush()  # populates project.id without committing
    await db.refresh(project)
    return project


async def add_owner_member(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    email: str = "",
) -> ProjectMember:
    """Insert the initial owner row for a newly created project."""
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        name=name,
        email=email,
        role=MemberRole.OWNER,
    )
    db.add(member)
    await db.flush()
    return member


@dataclass
class ProjectRow:
    """Flat projection used by list / detail queries."""

    project: Project
    caller_role: str
    member_count: int


async def list_for_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    offset: int,
    limit: int,
) -> list[ProjectRow]:
    """
    Return projects where ``user_id`` is a member (not soft-deleted),
    ordered by ``updated_at DESC``.
    """
    member_count_sq = (
        select(func.count())
        .where(ProjectMember.project_id == Project.id)
        .correlate(Project)
        .scalar_subquery()
    )
    stmt = (
        select(Project, ProjectMember.role, member_count_sq.label("member_count"))
        .join(
            ProjectMember,
            (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == user_id),
        )
        .where(Project.is_deleted.is_(False))
        .order_by(Project.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [
        ProjectRow(project=r.Project, caller_role=r.role.value, member_count=r.member_count)
        for r in rows
    ]


async def count_for_user(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Return total number of non-deleted projects the user is a member of."""
    result = await db.execute(
        select(func.count())
        .select_from(Project)
        .join(
            ProjectMember,
            (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == user_id),
        )
        .where(Project.is_deleted.is_(False))
    )
    return result.scalar_one()


async def get_detail_for_user(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ProjectRow | None:
    """Return a single project's detail plus the caller's role and member count."""
    member_count_sq = (
        select(func.count())
        .where(ProjectMember.project_id == Project.id)
        .correlate(Project)
        .scalar_subquery()
    )
    stmt = (
        select(Project, ProjectMember.role, member_count_sq.label("member_count"))
        .join(
            ProjectMember,
            (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == user_id),
        )
        .where(Project.id == project_id, Project.is_deleted.is_(False))
    )
    row = (await db.execute(stmt)).one_or_none()
    if row is None:
        return None
    return ProjectRow(
        project=row.Project, caller_role=row.role.value, member_count=row.member_count
    )


async def update_fields(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    updated_at: datetime,
) -> None:
    """Partial update of mutable project fields."""
    values: dict = {"updated_at": updated_at}
    if name is not None:
        values["name"] = name
    if description is not None:
        values["description"] = description
    await db.execute(update(Project).where(Project.id == project_id).values(**values))


async def soft_delete(db: AsyncSession, project_id: uuid.UUID) -> None:
    """Set is_deleted=True on the project row."""
    await db.execute(update(Project).where(Project.id == project_id).values(is_deleted=True))


async def count_by_key_prefix(db: AsyncSession, base: str) -> int:
    """
    Count existing keys that equal ``base`` or match ``base<N>``.
    Used to decide whether a suffix is needed without a full table scan.
    """
    result = await db.execute(select(func.count()).where(Project.key.like(f"{base}%")))
    return result.scalar_one()


async def get_for_update(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """Return the project row with a FOR UPDATE lock (serialises concurrent transfers).

    FOR UPDATE is silently ignored on SQLite, which is fine for tests.
    """
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.is_deleted.is_(False))
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def update_owner(db: AsyncSession, project_id: uuid.UUID, new_owner_id: uuid.UUID) -> None:
    """Set the owner_id on the project row."""
    await db.execute(
        update(Project).where(Project.id == project_id).values(owner_id=new_owner_id)
    )
