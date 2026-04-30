"""
Epics API router.

Endpoints
---------
POST   /api/v1/projects/{project_id}/epics            create an epic (member)
GET    /api/v1/projects/{project_id}/epics            paginated list with progress (member)
GET    /api/v1/projects/{project_id}/epics/{epic_id}  detail (member)
PATCH  /api/v1/projects/{project_id}/epics/{epic_id}  update name/description (member)
DELETE /api/v1/projects/{project_id}/epics/{epic_id}  soft-delete + unlink stories (member; gated)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership, get_current_user, require_member
from app.core.database import get_db
from app.schemas.common import Envelope
from app.schemas.epic import EpicCreate, EpicOut
from app.services import epic as epic_service
from app.utils.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/projects/{project_id}/epics", tags=["epics"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Envelope[EpicOut])
async def create_epic(
    body: EpicCreate,
    membership: ProjectMembership = Depends(require_member),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Envelope[EpicOut]:
    epic = await epic_service.create_epic(
        db,
        membership=membership,
        user=user,
        name=body.name,
        description=body.description,
    )
    return Envelope(message="Epic created", data=epic)


@router.get("", response_model=Envelope[list[EpicOut]])
async def list_epics(
    page: int = Query(DEFAULT_PAGE, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, alias="pageSize"),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[list[EpicOut]]:
    items, pagination = await epic_service.list_epics(
        db, membership=membership, page=page, page_size=page_size
    )
    return Envelope(data=items, pagination=pagination)


@router.get("/{epic_id}", response_model=Envelope[EpicOut])
async def get_epic(
    epic_id: UUID = Path(...),
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> Envelope[EpicOut]:
    epic = await epic_service.get_epic(db, epic_id=epic_id, membership=membership)
    return Envelope(data=epic)
