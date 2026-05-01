"""
Comment repository — raw SQLAlchemy queries.

All functions flush but do NOT commit — the service layer owns transaction
boundaries so it can fire events after the commit.
"""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


async def create(
    db: AsyncSession,
    *,
    user_story_id: uuid.UUID,
    author_id: uuid.UUID,
    body: str,
    image_url: str | None,
) -> Comment:
    """Insert a new comment and flush (does NOT commit)."""
    comment = Comment(
        user_story_id=user_story_id,
        author_id=author_id,
        body=body,
        image_url=image_url,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    return comment


async def get_by_id(db: AsyncSession, comment_id: uuid.UUID) -> Comment | None:
    """
    Fetch a comment by PK with no soft-delete filter applied.

    The service layer decides whether a deleted comment should be a 404.
    """
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    return result.scalar_one_or_none()


async def list_for_story(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    page: int,
    page_size: int,
) -> tuple[list[Comment], int]:
    """
    Return active (non-deleted) comments for a story, ordered oldest-first.

    Returns ``(rows, total_count)`` for pagination metadata.
    """
    base = select(Comment).where(
        Comment.user_story_id == story_id,
        Comment.is_deleted.is_(False),
    )

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = total_result.scalar_one()

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base.order_by(Comment.created_at.asc()).offset(offset).limit(page_size)
    )
    return list(rows_result.scalars().all()), total


async def soft_delete(db: AsyncSession, comment_id: uuid.UUID) -> None:
    """Set is_deleted=True. Does NOT commit."""
    await db.execute(update(Comment).where(Comment.id == comment_id).values(is_deleted=True))
