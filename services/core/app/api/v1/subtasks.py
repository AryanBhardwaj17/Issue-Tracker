"""
Subtasks API router — CRUD for subtasks nested under a parent task.

Endpoints
---------
POST   /api/v1/projects/{project_id}/tasks/{task_id}/subtasks               create subtask
GET    /api/v1/projects/{project_id}/tasks/{task_id}/subtasks               list subtasks
PATCH  /api/v1/projects/{project_id}/tasks/{task_id}/subtasks/{subtask_id}  update subtask
DELETE /api/v1/projects/{project_id}/tasks/{task_id}/subtasks/{subtask_id}  delete subtask
"""

import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    CurrentUser,
    ProjectMembership,
    get_current_user,
    require_member,
)
from app.core.database import get_db
from app.schemas.common import Envelope
from app.schemas.task import SubtaskOut, TaskCreateRequest, TaskOut, TaskUpdateRequest
from app.services import task as task_service
from app.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

router = APIRouter(
    prefix="/projects/{project_id}/tasks/{task_id}",
    tags=["subtasks"],
)


@router.post(
    "/subtasks",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[SubtaskOut],
)
async def create_subtask(
    task_id: uuid.UUID,
    body: TaskCreateRequest,
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[SubtaskOut]:
    subtask = await task_service.create_subtask(
        db,
        parent_task_id=task_id,
        project_id=membership.project_id,
        data=body,
        user=user,
    )
    return Envelope(message="Subtask created", data=subtask)


@router.get(
    "/subtasks",
    response_model=Envelope[list[SubtaskOut]],
)
async def list_subtasks(
    task_id: uuid.UUID,
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
) -> Envelope[list[SubtaskOut]]:
    subtasks, pagination = await task_service.list_subtasks(
        db,
        parent_task_id=task_id,
        project_id=membership.project_id,
        page=page,
        page_size=page_size,
    )
    return Envelope(data=subtasks, pagination=pagination)


@router.patch(
    "/subtasks/{subtask_id}",
    response_model=Envelope[TaskOut],
)
async def update_subtask(
    subtask_id: uuid.UUID,
    body: TaskUpdateRequest,
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[TaskOut]:
    task = await task_service.update_task(
        db,
        task_id=subtask_id,
        project_id=membership.project_id,
        data=body,
        user=user,
        membership=membership,
    )
    return Envelope(data=task)


@router.delete(
    "/subtasks/{subtask_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subtask(
    subtask_id: uuid.UUID,
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await task_service.soft_delete_task(
        db,
        task_id=subtask_id,
        project_id=membership.project_id,
        user=user,
        membership=membership,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
