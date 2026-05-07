"""
Epic comments router — CRUD endpoints for comments on epics.

Endpoints
---------
POST   /projects/{project_id}/epics/{epic_id}/comments
GET    /projects/{project_id}/epics/{epic_id}/comments
PATCH  /projects/{project_id}/epics/{epic_id}/comments/{comment_id}
DELETE /projects/{project_id}/epics/{epic_id}/comments/{comment_id}
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
    prefix="/projects/{project_id}/epics/{epic_id}/comments",
    tags=["epic-comments"],
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Envelope[CommentOut])
async def create_epic_comment(
    body: CommentCreate,
    epic_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[CommentOut]:
    comment = await comment_service.create_epic_comment(
        db, epic_id=epic_id, user=user, membership=membership, body_data=body
    )
    return Envelope(message="Comment created", data=comment)


@router.get("", response_model=Envelope[list[CommentOut]])
async def list_epic_comments(
    epic_id: UUID = Path(...),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[CommentOut]]:
    items, pagination = await comment_service.list_epic_comments(
        db, epic_id=epic_id, membership=membership, page=page, page_size=page_size
    )
    return Envelope(data=items, pagination=pagination)


@router.patch("/{comment_id}", response_model=Envelope[CommentOut])
async def edit_epic_comment(
    body: CommentUpdate,
    epic_id: UUID = Path(...),
    comment_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[CommentOut]:
    comment = await comment_service.edit_epic_comment(
        db,
        epic_id=epic_id,
        comment_id=comment_id,
        user=user,
        membership=membership,
        body_data=body,
    )
    return Envelope(message="Comment updated", data=comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_epic_comment(
    epic_id: UUID = Path(...),
    comment_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await comment_service.delete_epic_comment(
        db, epic_id=epic_id, comment_id=comment_id, user=user, membership=membership
    )
