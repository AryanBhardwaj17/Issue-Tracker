"""
Projects API router — 5 endpoints for Project CRUD.

Endpoints
---------
POST   /api/v1/projects              create a project (authenticated)
GET    /api/v1/projects              list caller's projects (authenticated)
GET    /api/v1/projects/{project_id} get project detail (member only)
PATCH  /api/v1/projects/{project_id} update project (owner only)
DELETE /api/v1/projects/{project_id} soft-delete project (owner only)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    CurrentUser,
    ProjectMembership,
    get_current_user,
    require_member,
    require_owner,
)
from app.core.database import get_db
from app.schemas.common import Envelope
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListItem,
    ProjectOut,
    ProjectUpdateRequest,
)
from app.services import project as project_service
from app.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Envelope[ProjectOut])
async def create_project(
    body: ProjectCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[ProjectOut]:
    project = await project_service.create_project(
        db, user=user, name=body.name, description=body.description
    )
    return Envelope(message="Project created", data=project)


@router.get("", response_model=Envelope[list[ProjectListItem]])
async def list_projects(
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[ProjectListItem]]:
    items, pagination = await project_service.list_projects(
        db, user=user, page=page, page_size=page_size
    )
    return Envelope(data=items, pagination=pagination)


@router.get("/{project_id}", response_model=Envelope[ProjectOut])
async def get_project(
    project_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[ProjectOut]:
    project = await project_service.get_project(db, project_id=membership.project_id, user=user)
    return Envelope(data=project)


@router.patch("/{project_id}", response_model=Envelope[ProjectOut])
async def update_project(
    body: ProjectUpdateRequest,
    project_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> Envelope[ProjectOut]:
    project = await project_service.update_project(
        db, project_id=membership.project_id, data=body, membership=membership
    )
    return Envelope(message="Project updated", data=project)


@router.delete("/{project_id}", response_model=Envelope[None])
async def delete_project(
    project_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> Envelope[None]:
    await project_service.soft_delete_project(db, project_id=membership.project_id)
    return Envelope(message="Project deleted")
