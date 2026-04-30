"""
FastAPI dependency functions for the Core Service.

Provides:
- ``get_current_user``   — verifies the RS256 JWT and returns a CurrentUser.
- ``require_member``     — asserts the caller is a member of the given project.
- ``require_owner``      — asserts the caller is the project owner.
"""

import uuid
from dataclasses import dataclass
from typing import Literal

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, InvalidTokenError, ProjectNotFoundError
from app.core.security import decode_access_token
from app.grpc.client import AuthGrpcClient
from app.models.project_member import MemberRole
from app.repositories import project as project_repo
from app.repositories import project_members as member_repo


@dataclass
class CurrentUser:
    """Caller identity extracted from the verified JWT payload."""

    id: uuid.UUID
    name: str
    email: str


@dataclass
class ProjectMembership:
    """Caller's membership record for a specific project."""

    user_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    role: Literal["owner", "member"]


_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    """
    Extract and verify the RS256 JWT from the ``Authorization: Bearer <token>`` header.

    Raises 401 on missing, malformed, expired, or tampered tokens.
    """
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise InvalidTokenError()

    try:
        user_id = uuid.UUID(payload["sub"])
        name: str = payload["name"]
        email: str = payload["email"]
    except (KeyError, ValueError):
        raise InvalidTokenError()

    return CurrentUser(id=user_id, name=name, email=email)


async def require_member(
    project_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectMembership:
    """
    Assert the caller is an active member of the project.

    - 404 if the project does not exist or is soft-deleted.
    - 403 if the caller is not in ``project_members``.
    """
    project = await project_repo.get_by_id(db, project_id)
    if project is None:
        raise ProjectNotFoundError()

    member = await member_repo.get(db, project_id, user.id)
    if member is None:
        raise ForbiddenError("Not a project member")

    return ProjectMembership(
        user_id=user.id,
        project_id=project_id,
        name=member.name,
        role=member.role.value,  # MemberRole enum → str
    )


async def require_owner(
    membership: ProjectMembership = Depends(require_member),
) -> ProjectMembership:
    """
    Assert the caller is the project owner.

    - 403 if the caller's role is not ``owner``.
    """
    if membership.role != MemberRole.OWNER.value:
        raise ForbiddenError("Owner only")
    return membership


def get_grpc_client() -> AuthGrpcClient:
    """FastAPI dependency — returns the singleton gRPC client initialised in main.py."""
    from app.main import _grpc_client  # deferred import to avoid circular dependency

    assert _grpc_client is not None, "gRPC client not initialised"
    return _grpc_client
