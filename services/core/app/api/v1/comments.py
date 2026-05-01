"""
Comments router — 4 endpoints nested under a project story.

Endpoints
---------
POST   /projects/{project_id}/stories/{story_id}/comments
GET    /projects/{project_id}/stories/{story_id}/comments
PATCH  /projects/{project_id}/stories/{story_id}/comments/{comment_id}
DELETE /projects/{project_id}/stories/{story_id}/comments/{comment_id}

All write operations accept JSON bodies (not multipart).
Use POST /upload/image first to get a URL, then include it in the JSON body.
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

router = APIRouter(
    prefix="/projects/{project_id}/stories/{story_id}/comments",
    tags=["comments"],
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Envelope[CommentOut])
async def create_comment(
    body: CommentCreate,
    story_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[CommentOut]:
    comment = await comment_service.create_comment(
        db,
        story_id=story_id,
        user=user,
        membership=membership,
        body_data=body,
    )
    return Envelope(message="Comment created", data=comment)


@router.get("", response_model=Envelope[list[CommentOut]])
async def list_comments(
    story_id: UUID = Path(...),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[CommentOut]]:
    items, pagination = await comment_service.list_comments(
        db,
        story_id=story_id,
        membership=membership,
        page=page,
        page_size=page_size,
    )
    return Envelope(data=items, pagination=pagination)


@router.patch("/{comment_id}", response_model=Envelope[CommentOut])
async def edit_comment(
    body: CommentUpdate,
    story_id: UUID = Path(...),
    comment_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[CommentOut]:
    comment = await comment_service.edit_comment(
        db,
        story_id=story_id,
        comment_id=comment_id,
        user=user,
        membership=membership,
        body_data=body,
    )
    return Envelope(message="Comment updated", data=comment)


@router.delete("/{comment_id}", response_model=Envelope[None])
async def delete_comment(
    story_id: UUID = Path(...),
    comment_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[None]:
    await comment_service.delete_comment(
        db,
        story_id=story_id,
        comment_id=comment_id,
        user=user,
        membership=membership,
    )
    return Envelope(message="Comment deleted")
