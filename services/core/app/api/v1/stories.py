"""
Stories API router.

Endpoints
---------
POST   /projects/{project_id}/stories            create a story (member)
GET    /projects/{project_id}/stories             list with filters (member)
GET    /projects/{project_id}/stories/{story_id}  detail (member)
PATCH  /api/v1/projects/{project_id}/stories/{story_id}  partial update (member; per-field guards)
DELETE /api/v1/projects/{project_id}/stories/{story_id}  soft-delete + cascade (member; gated)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership, get_current_user, require_member
from app.core.database import get_db
from app.repositories import project as project_repo
from app.schemas.common import Envelope
from app.schemas.story import StoryCreate, StoryOut, StoryPatch
from app.services import story as story_service
from app.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/projects/{project_id}/stories", tags=["stories"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Envelope[StoryOut])
async def create_story(
    body: StoryCreate,
    project_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[StoryOut]:
    project = await project_repo.get_by_id(db, project_id)
    story = await story_service.create_story(db, project=project, user=user, body=body)
    return Envelope(message="Story created", data=story)


@router.get("", response_model=Envelope[list[StoryOut]])
async def list_stories(
    project_id: UUID = Path(...),
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    assignee_id: list[UUID] | None = Query(None, alias="assigneeId"),
    priority: list[str] | None = Query(None),
    story_status: list[str] | None = Query(None, alias="status"),
    epic_id: list[str] | None = Query(None, alias="epicId"),
    search: str | None = Query(None),
    sort_by: str = Query("priority", alias="sortBy"),
    sort_order: str = Query("desc", alias="sortOrder"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[StoryOut]]:
    # Parse epicId: accepts UUID strings + literal "none" for unlinked stories
    parsed_epic_ids: list[UUID | None] | None = None
    if epic_id is not None:
        parsed_epic_ids = []
        for eid in epic_id:
            if eid.lower() == "none":
                parsed_epic_ids.append(None)
            else:
                parsed_epic_ids.append(UUID(eid))

    items, pagination = await story_service.list_stories(
        db,
        membership=membership,
        page=page,
        page_size=page_size,
        assignee_ids=assignee_id,
        priorities=priority,
        statuses=story_status,
        epic_ids=parsed_epic_ids,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return Envelope(data=items, pagination=pagination)


@router.get("/{story_id}", response_model=Envelope[StoryOut])
async def get_story(
    story_id: UUID = Path(...),
    project_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[StoryOut]:
    story = await story_service.get_story(db, story_id=story_id, membership=membership)
    return Envelope(data=story)


@router.patch("/{story_id}", response_model=Envelope[StoryOut])
async def update_story(
    body: StoryPatch,
    story_id: UUID = Path(...),
    project_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[StoryOut]:
    from app.repositories import story as story_repo

    project = await project_repo.get_by_id(db, project_id)
    story = await story_repo.get_active(db, story_id, project_id)
    if story is None:
        from app.core.exceptions import StoryNotFoundError

        raise StoryNotFoundError()

    result = await story_service.update_story(
        db,
        story=story,
        project=project,
        user=user,
        membership=membership,
        body=body,
    )
    return Envelope(message="Story updated", data=result)


@router.delete("/{story_id}", status_code=status.HTTP_200_OK, response_model=Envelope[None])
async def delete_story(
    story_id: UUID = Path(...),
    project_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[None]:
    project = await project_repo.get_by_id(db, project_id)
    await story_service.delete_story(
        db, story_id=story_id, project=project, user=user, membership=membership
    )
    return Envelope(message="Story deleted", data=None)
