"""
Project-members service — business logic for adding members, listing them,
and transferring project ownership.

All DB I/O is delegated to the repository layer.  The gRPC client is used
to look up users in the Auth service by email.
"""

import logging
import uuid

from grpc import aio as grpc_aio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyMemberError,
    AuthServiceUnavailableError,
    BadRequestError,
    ForbiddenError,
    ProjectNotFoundError,
    UserNotFoundError,
)
from app.events import publisher
from app.events.constants import EVENT_MEMBER_ADDED, EVENT_OWNERSHIP_TRANSFERRED
from app.events.payloads import build_member_added_payload, build_ownership_transferred_payload
from app.grpc.client import AuthGrpcClient, AuthUser
from app.models.project_member import MemberRole
from app.repositories import project as project_repo
from app.repositories import project_members as member_repo
from app.schemas.project_members import MemberOut
from app.utils.constants import (
    ERR_NOT_CURRENT_MEMBER,
    ERR_SELF_TRANSFER,
)

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _member_to_out(member) -> MemberOut:
    """Map an ORM ProjectMember to a MemberOut response schema."""
    return MemberOut(
        id=member.id,
        user_id=member.user_id,
        name=member.name,
        email=member.email,
        role=member.role.value,
        joined_at=member.joined_at,
    )


# ── Add member by email ──────────────────────────────────────────────────────


async def add_member(
    db: AsyncSession,
    grpc_client: AuthGrpcClient,
    *,
    project_id: uuid.UUID,
    email: str,
    caller_id: uuid.UUID,
) -> MemberOut:
    """
    Add a user (looked up by email via Auth gRPC) to the project.

    Business rules:
    - Project must exist and not be soft-deleted.
    - Caller must be the project owner.
    - Target user must exist in Auth service.
    - Target must not already be a project member.
    """
    # 1. Validate project exists
    project = await project_repo.get_by_id(db, project_id)
    if project is None:
        raise ProjectNotFoundError()

    # 2. Validate caller is owner
    caller_member = await member_repo.get(db, project_id, caller_id)
    if caller_member is None or caller_member.role != MemberRole.OWNER:
        raise ForbiddenError("Owner only")

    # 3. Look up target user via gRPC
    normalized_email = email.strip().lower()
    try:
        auth_user: AuthUser | None = await grpc_client.get_user_by_email(normalized_email)
    except grpc_aio.AioRpcError:
        raise AuthServiceUnavailableError()

    if auth_user is None:
        raise UserNotFoundError()

    # 4. Check not already a member
    existing = await member_repo.get(db, project_id, auth_user.id)
    if existing is not None:
        raise AlreadyMemberError()

    # 5. Insert membership
    member = await member_repo.add_member(
        db,
        project_id=project_id,
        user_id=auth_user.id,
        name=auth_user.name,
        email=auth_user.email,
    )
    await db.commit()

    logger.info(
        "Member added: project=%s user=%s email=%s by=%s",
        project_id,
        auth_user.id,
        normalized_email,
        caller_id,
    )

    # 6. Publish event (fire-and-forget)
    await publisher.publish_event(
        EVENT_MEMBER_ADDED,
        build_member_added_payload(
            project_id=project_id,
            project_name=project.name,
            project_key=project.key,
            added_user_id=auth_user.id,
            added_user_email=auth_user.email,
            added_user_name=auth_user.name,
            actor_id=caller_id,
            actor_name=caller_member.name,
        ),
    )

    return _member_to_out(member)


# ── List members ──────────────────────────────────────────────────────────────


async def list_members(
    db: AsyncSession,
    grpc_client: AuthGrpcClient,
    *,
    project_id: uuid.UUID,
) -> list[MemberOut]:
    """
    Return all members of a project.  Email is now stored in the DB,
    so no gRPC round-trip is needed for listing.
    """
    members = await member_repo.list_members(db, project_id)
    return [_member_to_out(m) for m in members]


# ── Transfer ownership ────────────────────────────────────────────────────────


async def transfer_ownership(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    caller_id: uuid.UUID,
    caller_name: str,
    new_owner_id: uuid.UUID,
) -> None:
    """
    Transfer project ownership from the current owner to another member.

    Business rules:
    - Project must exist (locked with FOR UPDATE).
    - Caller must be the current owner.
    - new_owner_id must not equal caller_id (self-transfer).
    - new_owner_id must be a current project member.
    """
    # 1. Lock the project row
    project = await project_repo.get_for_update(db, project_id)
    if project is None:
        raise ProjectNotFoundError()

    # 2. Verify caller is current owner
    if project.owner_id != caller_id:
        raise ForbiddenError("Owner only")

    # 3. Self-transfer guard
    if new_owner_id == caller_id:
        raise BadRequestError(ERR_SELF_TRANSFER)

    # 4. Verify new owner is a current member
    new_owner_member = await member_repo.get(db, project_id, new_owner_id)
    if new_owner_member is None:
        raise BadRequestError(ERR_NOT_CURRENT_MEMBER)

    # 5. Swap roles
    await member_repo.update_role(db, project_id, caller_id, MemberRole.MEMBER)
    await member_repo.update_role(db, project_id, new_owner_id, MemberRole.OWNER)
    await project_repo.update_owner(db, project_id, new_owner_id)
    await db.commit()

    logger.info(
        "Ownership transferred: project=%s from=%s to=%s",
        project_id,
        caller_id,
        new_owner_id,
    )

    # 6. Publish event
    await publisher.publish_event(
        EVENT_OWNERSHIP_TRANSFERRED,
        build_ownership_transferred_payload(
            project_id=project_id,
            project_name=project.name,
            new_owner_id=new_owner_id,
            new_owner_email=new_owner_member.email,
            new_owner_name=new_owner_member.name,
            previous_owner_id=caller_id,
            previous_owner_name=caller_name,
            actor_id=caller_id,
        ),
    )
