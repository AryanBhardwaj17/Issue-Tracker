"""
Task & Subtask comments router — CRUD endpoints for comments on tasks and subtasks.

Endpoints
---------
POST   /projects/{project_id}/stories/{story_id}/tasks/{task_id}/comments
GET    /projects/{project_id}/stories/{story_id}/tasks/{task_id}/comments
PATCH  /projects/{project_id}/stories/{story_id}/tasks/{task_id}/comments/{comment_id}
DELETE /projects/{project_id}/stories/{story_id}/tasks/{task_id}/comments/{comment_id}

POST   /projects/{project_id}/stories/{story_id}/tasks/{task_id}/subtasks/{subtask_id}/comments
GET    /projects/{project_id}/stories/{story_id}/tasks/{task_id}/subtasks/{subtask_id}/comments
PATCH  .../subtasks/{subtask_id}/comments/{comment_id}
DELETE .../subtasks/{subtask_id}/comments/{comment_id}
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership, get_current_user, require_member
from app.core.database import get_db
from app.schemas.comment import CommentCreate, CommentOut, CommentUpdate
from app.schemas.common import Envelope
from app.services import comment as comment_service
from app.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(tags=["task-comments"])


# ── Task comments ─────────────────────────────────────────────────────────────


@router.post(
    "/projects/{project_id}/stories/{story_id}/tasks/{task_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[CommentOut],
)
async def create_task_comment(
    body: CommentCreate,
    task_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[CommentOut]:
    comment = await comment_service.create_task_comment(
        db, task_id=task_id, user=user, membership=membership, body_data=body
    )
    return Envelope(message="Comment created", data=comment)


@router.get(
    "/projects/{project_id}/stories/{story_id}/tasks/{task_id}/comments",
    response_model=Envelope[list[CommentOut]],
)
async def list_task_comments(
    task_id: UUID = Path(...),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[CommentOut]]:
    items, pagination = await comment_service.list_task_comments(
        db, task_id=task_id, membership=membership, page=page, page_size=page_size
    )
    return Envelope(data=items, pagination=pagination)


@router.patch(
    "/projects/{project_id}/stories/{story_id}/tasks/{task_id}/comments/{comment_id}",
    response_model=Envelope[CommentOut],
)
async def edit_task_comment(
    body: CommentUpdate,
    task_id: UUID = Path(...),
    comment_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[CommentOut]:
    comment = await comment_service.edit_task_comment(
        db,
        task_id=task_id,
        comment_id=comment_id,
        user=user,
        membership=membership,
        body_data=body,
    )
    return Envelope(message="Comment updated", data=comment)


@router.delete(
    "/projects/{project_id}/stories/{story_id}/tasks/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task_comment(
    task_id: UUID = Path(...),
    comment_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await comment_service.delete_task_comment(
        db, task_id=task_id, comment_id=comment_id, user=user, membership=membership
    )


# ── Subtask comments ──────────────────────────────────────────────────────────


@router.post(
    "/projects/{project_id}/stories/{story_id}/tasks/{task_id}/subtasks/{subtask_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[CommentOut],
)
async def create_subtask_comment(
    body: CommentCreate,
    subtask_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[CommentOut]:
    # Subtasks are tasks — use the same service function with the subtask_id
    comment = await comment_service.create_task_comment(
        db, task_id=subtask_id, user=user, membership=membership, body_data=body
    )
    return Envelope(message="Comment created", data=comment)


@router.get(
    "/projects/{project_id}/stories/{story_id}/tasks/{task_id}/subtasks/{subtask_id}/comments",
    response_model=Envelope[list[CommentOut]],
)
async def list_subtask_comments(
    subtask_id: UUID = Path(...),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[CommentOut]]:
    items, pagination = await comment_service.list_task_comments(
        db, task_id=subtask_id, membership=membership, page=page, page_size=page_size
    )
    return Envelope(data=items, pagination=pagination)


@router.patch(
    "/projects/{project_id}/stories/{story_id}/tasks/{task_id}/subtasks/{subtask_id}/comments/{comment_id}",
    response_model=Envelope[CommentOut],
)
async def edit_subtask_comment(
    body: CommentUpdate,
    subtask_id: UUID = Path(...),
    comment_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[CommentOut]:
    comment = await comment_service.edit_task_comment(
        db,
        task_id=subtask_id,
        comment_id=comment_id,
        user=user,
        membership=membership,
        body_data=body,
    )
    return Envelope(message="Comment updated", data=comment)


@router.delete(
    "/projects/{project_id}/stories/{story_id}/tasks/{task_id}/subtasks/{subtask_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subtask_comment(
    subtask_id: UUID = Path(...),
    comment_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await comment_service.delete_task_comment(
        db, task_id=subtask_id, comment_id=comment_id, user=user, membership=membership
    )
