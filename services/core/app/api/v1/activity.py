"""
Activity router — read-only endpoints for activity feeds.

Endpoints
---------
GET /projects/{project_id}/stories/{story_id}/activity
GET /projects/{project_id}/tasks/{task_id}/activity
GET /projects/{project_id}/epics/{epic_id}/activity
GET /projects/{project_id}/activity
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ProjectMembership, require_member
from app.core.database import get_db
from app.schemas.activity_log import ActivityLogOut
from app.schemas.common import Envelope
from app.services import activity_log as activity_service
from app.utils.constants import DEFAULT_PAGE, MAX_PAGE_SIZE

router = APIRouter(tags=["activity"])


@router.get(
    "/projects/{project_id}/stories/{story_id}/activity",
    response_model=Envelope[list[ActivityLogOut]],
)
async def get_story_activity(
    story_id: UUID = Path(...),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[ActivityLogOut]]:
    items, pagination = await activity_service.get_story_activity(
        db, story_id=story_id, membership=membership, page=page, page_size=page_size
    )
    return Envelope(data=items, pagination=pagination)


@router.get(
    "/projects/{project_id}/tasks/{task_id}/activity",
    response_model=Envelope[list[ActivityLogOut]],
)
async def get_task_activity(
    task_id: UUID = Path(...),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[ActivityLogOut]]:
    items, pagination = await activity_service.get_task_activity(
        db, task_id=task_id, membership=membership, page=page, page_size=page_size
    )
    return Envelope(data=items, pagination=pagination)


@router.get(
    "/projects/{project_id}/epics/{epic_id}/activity",
    response_model=Envelope[list[ActivityLogOut]],
)
async def get_epic_activity(
    epic_id: UUID = Path(...),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[ActivityLogOut]]:
    items, pagination = await activity_service.get_epic_activity(
        db, epic_id=epic_id, membership=membership, page=page, page_size=page_size
    )
    return Envelope(data=items, pagination=pagination)


@router.get(
    "/projects/{project_id}/activity",
    response_model=Envelope[list[ActivityLogOut]],
)
async def get_project_activity(
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[ActivityLogOut]]:
    items, pagination = await activity_service.get_project_activity(
        db, membership=membership, page=page, page_size=page_size
    )
    return Envelope(data=items, pagination=pagination)
