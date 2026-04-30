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

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership
from app.repositories import epic as epic_repo
from app.repositories import project_members as member_repo
from app.schemas.epic import EpicOut, EpicProgressOut, ReporterRef

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
    await db.commit()
    await db.refresh(epic)

    logger.info("Epic created: id=%s project=%s by user=%s", epic.id, epic.project_id, user.id)
    return _to_epic_out(epic, reporter_name=user.name)
