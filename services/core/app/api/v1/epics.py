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

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership, get_current_user, require_member
from app.core.database import get_db
from app.schemas.common import Envelope
from app.schemas.epic import EpicCreate, EpicOut
from app.services import epic as epic_service

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
