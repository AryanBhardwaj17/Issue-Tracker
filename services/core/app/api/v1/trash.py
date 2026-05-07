"""
Trash router — list soft-deleted stories and restore them.

Endpoints
---------
GET  /projects/{project_id}/trash
POST /projects/{project_id}/stories/{story_id}/restore
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership, get_current_user, require_member
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, StoryNotFoundError
from app.models.activity_log import ActivityAction, ActivityEntityType
from app.models.comment import Comment
from app.models.story import StoryStatus, UserStory
from app.models.task import Task
from app.schemas.common import Envelope, paginate
from app.schemas.story import StoryOut
from app.services.activity_log import log_activity
from app.services.story import _to_story_out
from app.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, ERR_OWNER_ONLY, MAX_PAGE_SIZE

router = APIRouter(tags=["trash"])


@router.get(
    "/projects/{project_id}/trash",
    response_model=Envelope[list[StoryOut]],
)
async def list_deleted_stories(
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[StoryOut]]:
    """List soft-deleted stories for the project. Any member can view."""
    base = select(UserStory).where(
        UserStory.project_id == membership.project_id,
        UserStory.is_deleted.is_(True),
    )

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = total_result.scalar_one()

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        base.order_by(UserStory.updated_at.desc()).offset(offset).limit(page_size)
    )
    stories = list(rows_result.scalars().all())

    items = [await _to_story_out(db, s, membership.project_id) for s in stories]
    pagination = paginate(page, page_size, total)
    return Envelope(data=items, pagination=pagination)


@router.post(
    "/projects/{project_id}/stories/{story_id}/restore",
    response_model=Envelope[StoryOut],
    status_code=status.HTTP_200_OK,
)
async def restore_story(
    story_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[StoryOut]:
    """
    Restore a soft-deleted story. Owner only.

    Restores the story and all its cascaded tasks/comments.
    Story status resets to backlog.
    """
    # Only project owner can restore
    if membership.role != "owner":
        raise ForbiddenError(ERR_OWNER_ONLY)

    # Fetch the deleted story
    result = await db.execute(
        select(UserStory).where(
            UserStory.id == story_id,
            UserStory.project_id == membership.project_id,
            UserStory.is_deleted.is_(True),
        )
    )
    story = result.scalar_one_or_none()
    if story is None:
        raise StoryNotFoundError("Story not found in trash")

    # Restore story — reset status to backlog
    story.is_deleted = False
    story.status = StoryStatus.BACKLOG

    # Restore cascaded tasks and subtasks
    await db.execute(update(Task).where(Task.story_id == story_id).values(is_deleted=False))

    # Restore cascaded comments (only story-scoped ones)
    await db.execute(
        update(Comment).where(Comment.user_story_id == story_id).values(is_deleted=False)
    )

    # Log activity: story restored
    await log_activity(
        db,
        project_id=membership.project_id,
        entity_type=ActivityEntityType.story,
        action=ActivityAction.restored,
        actor_id=user.id,
        actor_name=user.name,
        story_id=story_id,
    )

    await db.commit()
    await db.refresh(story)

    out = await _to_story_out(db, story, membership.project_id)
    return Envelope(message="Story restored", data=out)
