"""
UserStory repository — raw SQLAlchemy queries for the Story aggregate.
"""

import uuid

from sqlalchemy import case, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.story import Priority, StoryStatus, UserStory


# ── Atomic story-key generation ───────────────────────────────────────────────


async def next_story_key(db: AsyncSession, project_id: uuid.UUID, project_key: str) -> str:
    """
    Atomically increment ``projects.next_story_seq`` and return the new story key.

    Must run inside the same transaction as the story INSERT so a rollback
    also rolls back the sequence increment.

    Falls back to a SELECT+UPDATE path for SQLite (used in tests).
    """
    dialect = db.bind.dialect.name if db.bind else "postgresql"

    if dialect == "sqlite":
        from app.models.project import Project

        result = await db.execute(
            select(Project.next_story_seq).where(Project.id == project_id)
        )
        current_seq = result.scalar_one()
        new_seq = current_seq + 1
        await db.execute(
            update(Project).where(Project.id == project_id).values(next_story_seq=new_seq)
        )
        return f"{project_key}-{new_seq}"

    result = await db.execute(
        text(
            "UPDATE projects SET next_story_seq = next_story_seq + 1 "
            "WHERE id = :pid RETURNING next_story_seq"
        ),
        {"pid": project_id},
    )
    seq = result.scalar_one()
    return f"{project_key}-{seq}"


# ── CRUD ──────────────────────────────────────────────────────────────────────


async def create(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    story_key: str,
    title: str,
    description: str | None,
    epic_id: uuid.UUID | None,
    status: StoryStatus,
    priority: Priority,
    story_points: int | None,
    assignee_id: uuid.UUID | None,
    reporter_id: uuid.UUID,
    due_date=None,
) -> UserStory:
    """Insert a new story row, flush, and return it."""
    story = UserStory(
        project_id=project_id,
        story_key=story_key,
        title=title,
        description=description,
        epic_id=epic_id,
        status=status,
        priority=priority,
        story_points=story_points,
        assignee_id=assignee_id,
        reporter_id=reporter_id,
        due_date=due_date,
    )
    db.add(story)
    await db.flush()
    await db.refresh(story)
    return story


async def get_by_id(db: AsyncSession, story_id: uuid.UUID) -> UserStory | None:
    """Return a story if it exists and is not soft-deleted, else None."""
    result = await db.execute(
        select(UserStory).where(UserStory.id == story_id, UserStory.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def get_active(
    db: AsyncSession,
    story_id: uuid.UUID,
    project_id: uuid.UUID,
) -> UserStory | None:
    """Return the story if it exists, belongs to the project, and is not soft-deleted."""
    result = await db.execute(
        select(UserStory).where(
            UserStory.id == story_id,
            UserStory.project_id == project_id,
            UserStory.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def soft_delete(db: AsyncSession, story_id: uuid.UUID) -> None:
    """Set is_deleted=True on a story."""
    await db.execute(
        update(UserStory).where(UserStory.id == story_id).values(is_deleted=True)
    )


# ── List / Filter / Sort / Search ────────────────────────────────────────────

PRIORITY_RANK = case(
    (UserStory.priority == Priority.CRITICAL, 4),
    (UserStory.priority == Priority.HIGH, 3),
    (UserStory.priority == Priority.MEDIUM, 2),
    (UserStory.priority == Priority.LOW, 1),
    else_=0,
)


def _escape_like(value: str) -> str:
    """Escape SQL LIKE wildcards so user input is treated literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _build_base_query(
    project_id: uuid.UUID,
    *,
    assignee_ids: list[uuid.UUID] | None = None,
    priorities: list[str] | None = None,
    statuses: list[str] | None = None,
    epic_ids: list[uuid.UUID | None] | None = None,
    search: str | None = None,
):
    """Build the WHERE-filtered SELECT for stories."""
    q = select(UserStory).where(
        UserStory.project_id == project_id,
        UserStory.is_deleted.is_(False),
    )

    if assignee_ids:
        q = q.where(UserStory.assignee_id.in_(assignee_ids))

    if priorities:
        q = q.where(UserStory.priority.in_(priorities))

    if statuses:
        q = q.where(UserStory.status.in_(statuses))

    if epic_ids is not None:
        has_none = None in epic_ids
        non_null_ids = [eid for eid in epic_ids if eid is not None]

        if has_none and not non_null_ids:
            q = q.where(UserStory.epic_id.is_(None))
        elif has_none and non_null_ids:
            q = q.where(
                or_(UserStory.epic_id.is_(None), UserStory.epic_id.in_(non_null_ids))
            )
        elif non_null_ids:
            q = q.where(UserStory.epic_id.in_(non_null_ids))

    if search:
        escaped = _escape_like(search)
        q = q.where(UserStory.title.ilike(f"%{escaped}%"))

    return q


def _apply_sort(q, sort_by: str, sort_order: str):
    """Apply ORDER BY clause. Always adds created_at DESC as secondary sort."""
    if sort_by == "priority":
        col = PRIORITY_RANK
    elif sort_by == "created_at":
        col = UserStory.created_at
    elif sort_by == "updated_at":
        col = UserStory.updated_at
    elif sort_by == "due_date":
        col = UserStory.due_date
    elif sort_by == "story_key":
        col = UserStory.story_key
    else:
        col = PRIORITY_RANK

    if sort_order == "asc":
        q = q.order_by(col.asc(), UserStory.created_at.desc())
    else:
        q = q.order_by(col.desc(), UserStory.created_at.desc())

    return q


async def list_filtered(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    page: int,
    page_size: int,
    assignee_ids: list[uuid.UUID] | None = None,
    priorities: list[str] | None = None,
    statuses: list[str] | None = None,
    epic_ids: list[uuid.UUID | None] | None = None,
    search: str | None = None,
    sort_by: str = "priority",
    sort_order: str = "desc",
) -> tuple[list[UserStory], int]:
    """Return (rows, total) for the filtered story list."""
    base = _build_base_query(
        project_id,
        assignee_ids=assignee_ids,
        priorities=priorities,
        statuses=statuses,
        epic_ids=epic_ids,
        search=search,
    )

    # Total count
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    total = total or 0

    # Apply sort + paginate
    q = _apply_sort(base, sort_by, sort_order)
    offset = (page - 1) * page_size
    result = await db.execute(q.offset(offset).limit(page_size))
    rows = list(result.scalars().all())

    return rows, total