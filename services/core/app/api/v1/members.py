"""
Members API router — endpoints for project membership and ownership transfer.

Endpoints
---------
POST   /api/v1/projects/{project_id}/members              add member by email (owner only)
GET    /api/v1/projects/{project_id}/members              list project members (member)
POST   /api/v1/projects/{project_id}/transfer-ownership   transfer ownership (owner only)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    ProjectMembership,
    get_grpc_client,
    require_member,
    require_owner,
)
from app.core.database import get_db
from app.grpc.client import AuthGrpcClient
from app.schemas.common import Envelope
from app.schemas.project_members import AddMemberRequest, MemberOut, TransferOwnershipRequest
from app.services import project_members as member_service

router = APIRouter(prefix="/projects/{project_id}", tags=["members"])


@router.post(
    "/members",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[MemberOut],
)
async def add_member(
    body: AddMemberRequest,
    membership: ProjectMembership = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
    grpc_client: AuthGrpcClient = Depends(get_grpc_client),
) -> Envelope[MemberOut]:
    member = await member_service.add_member(
        db,
        grpc_client,
        project_id=membership.project_id,
        email=body.email,
        caller_id=membership.user_id,
    )
    return Envelope(message="Member added", data=member)


@router.get(
    "/members",
    response_model=Envelope[list[MemberOut]],
)
async def list_members(
    membership: ProjectMembership = Depends(require_member),
    db: AsyncSession = Depends(get_db),
    grpc_client: AuthGrpcClient = Depends(get_grpc_client),
) -> Envelope[list[MemberOut]]:
    members = await member_service.list_members(
        db,
        grpc_client,
        project_id=membership.project_id,
    )
    return Envelope(data=members)


@router.post(
    "/transfer-ownership",
    response_model=Envelope[None],
)
async def transfer_ownership(
    body: TransferOwnershipRequest,
    membership: ProjectMembership = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> Envelope[None]:
    await member_service.transfer_ownership(
        db,
        project_id=membership.project_id,
        caller_id=membership.user_id,
        new_owner_id=body.new_owner_id,
    )
    return Envelope(message="Ownership transferred")
