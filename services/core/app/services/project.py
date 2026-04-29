"""
Project service — business logic for the Project aggregate.

Responsibilities:
- Project key generation (``extract_key_base``, ``_next_unique_key``).
- Full CRUD: create, list, get, update, soft-delete.
- Cascade soft-delete to all descendant rows.

All DB I/O is delegated to ``repositories.project`` and
``repositories.project_members``.
"""

import re
import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership
from app.core.exceptions import KeyGenerationError, ProjectNotFoundError
from app.models.project import Project
from app.models.project_member import MemberRole
from app.repositories import project as project_repo
from app.repositories import project_members as member_repo
from app.schemas.common import Pagination, paginate
from app.schemas.project import OwnerOut, ProjectListItem, ProjectOut, ProjectUpdateRequest
from app.utils.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    KEY_BASE_MAX_LETTERS,
    MAX_KEY_RETRIES,
    MAX_PAGE_SIZE,
)

# ── Key generation ────────────────────────────────────────────────────────────


def extract_key_base(name: str) -> str:
    """
    Derive the base key from a project name.

    Takes up to ``KEY_BASE_MAX_LETTERS`` (4) ASCII alphabetic characters
    from the name, uppercased.  Raises ``ValueError`` if no ASCII letters
    are present (caller should surface this as a 422 before reaching here).

    Examples::

        extract_key_base("Shop Front")  # -> "SHOP"
        extract_key_base("Go!")         # -> "GO"
        extract_key_base("123")         # -> ValueError
    """
    letters = re.sub(r"[^A-Za-z]", "", name)
    if not letters:
        raise ValueError("Project name must contain at least one ASCII letter")
    return letters[:KEY_BASE_MAX_LETTERS].upper()


async def _next_unique_key(db: AsyncSession, base: str) -> str:
    """
    Return the first available key starting from ``base``.

    Tries ``base`` first; on collision tries ``base1``, ``base2``, …
    up to ``MAX_KEY_RETRIES``.  The DB ``UNIQUE`` constraint is the
    authoritative guard — this pre-check just avoids unnecessary retries.
    """
    for attempt in range(MAX_KEY_RETRIES):
        candidate = base if attempt == 0 else f"{base}{attempt}"
        existing = await project_repo.get_by_key(db, candidate)
        if existing is None:
            return candidate
    raise KeyGenerationError()


# ── CRUD helpers ──────────────────────────────────────────────────────────────


def _to_project_out(
    project: Project,
    caller_role: str,
    member_count: int,
    owner_name: str,
) -> ProjectOut:
    return ProjectOut(
        id=project.id,
        name=project.name,
        key=project.key,
        description=project.description,
        owner=OwnerOut(id=project.owner_id, name=owner_name),
        role=caller_role,
        member_count=member_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


# ── Service functions ─────────────────────────────────────────────────────────


async def create_project(
    db: AsyncSession,
    *,
    user: CurrentUser,
    name: str,
    description: str | None,
) -> ProjectOut:
    """
    Create a new project and auto-add the creator as owner.

    Retries on ``IntegrityError`` (concurrent key collision) up to
    ``MAX_KEY_RETRIES`` times before raising ``KeyGenerationError``.
    """
    base = extract_key_base(name)

    for _ in range(MAX_KEY_RETRIES):
        key = await _next_unique_key(db, base)
        try:
            project = await project_repo.create(
                db, name=name, key=key, description=description, owner_id=user.id
            )
            await project_repo.add_owner_member(
                db, project_id=project.id, user_id=user.id, name=user.name
            )
            await db.commit()
            await db.refresh(project)

            return _to_project_out(
                project,
                caller_role=MemberRole.OWNER.value,
                member_count=1,
                owner_name=user.name,
            )
        except IntegrityError:
            await db.rollback()
            continue

    raise KeyGenerationError()


async def list_projects(
    db: AsyncSession,
    *,
    user: CurrentUser,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[ProjectListItem], Pagination]:
    """Return paginated projects the caller is a member of (not soft-deleted)."""
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    total = await project_repo.count_for_user(db, user.id)
    rows = await project_repo.list_for_user(db, user.id, offset=offset, limit=page_size)

    items = [
        ProjectListItem(
            id=r.project.id,
            name=r.project.name,
            key=r.project.key,
            description=r.project.description,
            role=r.caller_role,
            member_count=r.member_count,
            created_at=r.project.created_at,
            updated_at=r.project.updated_at,
        )
        for r in rows
    ]
    return items, paginate(page, page_size, total)


async def get_project(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    user: CurrentUser,
) -> ProjectOut:
    """
    Return full project detail for the caller.

    Raises ``ProjectNotFoundError`` (404) if the project does not exist,
    is soft-deleted, or the caller is not a member.
    """
    row = await project_repo.get_detail_for_user(db, project_id, user.id)
    if row is None:
        raise ProjectNotFoundError()

    # Resolve owner name from the members table (owner is always a member)
    owner_member = await member_repo.get(db, project_id, row.project.owner_id)
    owner_name = owner_member.name if owner_member else ""

    return _to_project_out(row.project, row.caller_role, row.member_count, owner_name)


async def update_project(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    data: ProjectUpdateRequest,
    membership: ProjectMembership,
) -> ProjectOut:
    """
    Partial update of ``name`` and/or ``description``.  ``key`` is immutable.
    Owner-only — caller must pass a ``ProjectMembership`` with role ``owner``.
    """
    now = datetime.now(UTC)
    await project_repo.update_fields(
        db,
        project_id,
        name=data.name,
        description=data.description,
        updated_at=now,
    )
    await db.commit()

    # Re-fetch updated row
    row = await project_repo.get_detail_for_user(db, project_id, membership.user_id)
    if row is None:  # pragma: no cover
        raise ProjectNotFoundError()

    owner_member = await member_repo.get(db, project_id, row.project.owner_id)
    owner_name = owner_member.name if owner_member else ""
    return _to_project_out(row.project, row.caller_role, row.member_count, owner_name)


async def soft_delete_project(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
) -> None:
    """
    Soft-delete the project and cascade ``is_deleted=True`` to all
    descendants (epics, stories, tasks, comments).
    """
    from app.services.cascade import cascade_soft_delete_project  # local import avoids circular

    await cascade_soft_delete_project(db, project_id)
    await db.commit()
