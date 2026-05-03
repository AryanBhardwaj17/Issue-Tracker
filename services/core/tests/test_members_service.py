"""
Tests for the project-members service: add_member, list_members, transfer_ownership.

Uses an in-memory SQLite DB and a mocked gRPC client (AuthGrpcClient).
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from grpc import aio as grpc_aio
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.core.exceptions import (
    AlreadyMemberError,
    AuthServiceUnavailableError,
    BadRequestError,
    ForbiddenError,
    ProjectNotFoundError,
    UserNotFoundError,
)
from app.grpc.client import AuthGrpcClient, AuthUser
from app.models.project import Project
from app.models.project_member import MemberRole
from app.repositories import project as project_repo
from app.repositories import project_members as member_repo
from app.services import project_members as member_service

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _seed_project(
    db: AsyncSession,
    owner: CurrentUser,
    name: str = "Test Project",
) -> Project:
    """Insert a project with the owner as a member.  Returns the project."""
    project = await project_repo.create(
        db,
        name=name,
        key=name[:4].upper(),
        description=None,
        owner_id=owner.id,
    )
    await project_repo.add_owner_member(
        db,
        project_id=project.id,
        user_id=owner.id,
        name=owner.name,
        email=owner.email,
    )
    await db.commit()
    return project


# ── add_member ────────────────────────────────────────────────────────────────


class TestAddMember:
    @pytest.mark.asyncio
    async def test_add_member_success(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        grpc_client_mock: AuthGrpcClient,
    ):
        project = await _seed_project(db, user_alice)

        target = AuthUser(
            id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
            name="Diana",
            email="diana@example.com",
        )
        grpc_client_mock.get_user_by_email = AsyncMock(return_value=target)

        result = await member_service.add_member(
            db,
            grpc_client_mock,
            project_id=project.id,
            email="diana@example.com",
            caller_id=user_alice.id,
        )

        assert result.user_id == target.id
        assert result.name == "Diana"
        assert result.email == "diana@example.com"
        assert result.role == "member"

    @pytest.mark.asyncio
    async def test_add_member_project_not_found(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        grpc_client_mock: AuthGrpcClient,
    ):
        with pytest.raises(ProjectNotFoundError):
            await member_service.add_member(
                db,
                grpc_client_mock,
                project_id=uuid.uuid4(),
                email="diana@example.com",
                caller_id=user_alice.id,
            )

    @pytest.mark.asyncio
    async def test_add_member_not_owner(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        grpc_client_mock: AuthGrpcClient,
    ):
        project = await _seed_project(db, user_alice)

        # Add bob as a regular member
        await member_repo.add_member(
            db,
            project_id=project.id,
            user_id=user_bob.id,
            name=user_bob.name,
            email=user_bob.email,
        )
        await db.commit()

        with pytest.raises(ForbiddenError, match="Owner only"):
            await member_service.add_member(
                db,
                grpc_client_mock,
                project_id=project.id,
                email="diana@example.com",
                caller_id=user_bob.id,
            )

    @pytest.mark.asyncio
    async def test_add_member_user_not_found(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        grpc_client_mock: AuthGrpcClient,
    ):
        project = await _seed_project(db, user_alice)
        grpc_client_mock.get_user_by_email = AsyncMock(return_value=None)

        with pytest.raises(UserNotFoundError):
            await member_service.add_member(
                db,
                grpc_client_mock,
                project_id=project.id,
                email="nobody@example.com",
                caller_id=user_alice.id,
            )

    @pytest.mark.asyncio
    async def test_add_member_already_member(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        grpc_client_mock: AuthGrpcClient,
    ):
        project = await _seed_project(db, user_alice)

        # Add bob as a member
        await member_repo.add_member(
            db,
            project_id=project.id,
            user_id=user_bob.id,
            name=user_bob.name,
        )
        await db.commit()

        target = AuthUser(id=user_bob.id, name=user_bob.name, email=user_bob.email)
        grpc_client_mock.get_user_by_email = AsyncMock(return_value=target)

        with pytest.raises(AlreadyMemberError):
            await member_service.add_member(
                db,
                grpc_client_mock,
                project_id=project.id,
                email="bob@example.com",
                caller_id=user_alice.id,
            )

    @pytest.mark.asyncio
    async def test_add_member_auth_service_unavailable(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        grpc_client_mock: AuthGrpcClient,
    ):
        project = await _seed_project(db, user_alice)
        grpc_client_mock.get_user_by_email = AsyncMock(
            side_effect=grpc_aio.AioRpcError(
                code=grpc_aio.AioRpcError,
                initial_metadata=None,
                trailing_metadata=None,
                details="unavailable",
            ),
        )

        with pytest.raises(AuthServiceUnavailableError):
            await member_service.add_member(
                db,
                grpc_client_mock,
                project_id=project.id,
                email="diana@example.com",
                caller_id=user_alice.id,
            )

    @pytest.mark.asyncio
    async def test_add_member_email_normalized(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        grpc_client_mock: AuthGrpcClient,
    ):
        """Email should be stripped and lowercased before lookup."""
        project = await _seed_project(db, user_alice)

        target = AuthUser(
            id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
            name="Diana",
            email="diana@example.com",
        )
        grpc_client_mock.get_user_by_email = AsyncMock(return_value=target)

        await member_service.add_member(
            db,
            grpc_client_mock,
            project_id=project.id,
            email="  DIANA@Example.COM  ",
            caller_id=user_alice.id,
        )

        grpc_client_mock.get_user_by_email.assert_called_once_with("diana@example.com")


# ── list_members ──────────────────────────────────────────────────────────────


class TestListMembers:
    @pytest.mark.asyncio
    async def test_list_members_success(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        grpc_client_mock: AuthGrpcClient,
    ):
        project = await _seed_project(db, user_alice)
        await member_repo.add_member(
            db,
            project_id=project.id,
            user_id=user_bob.id,
            name=user_bob.name,
            email=user_bob.email,
        )
        await db.commit()

        result = await member_service.list_members(
            db,
            grpc_client_mock,
            project_id=project.id,
        )

        assert len(result) == 2
        emails = {m.email for m in result}
        assert "alice@example.com" in emails
        assert "bob@example.com" in emails

    @pytest.mark.asyncio
    async def test_list_members_empty_project(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        grpc_client_mock: AuthGrpcClient,
    ):
        """A project with only the owner should return one member."""
        project = await _seed_project(db, user_alice)

        result = await member_service.list_members(
            db,
            grpc_client_mock,
            project_id=project.id,
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_members_returns_stored_email(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        grpc_client_mock: AuthGrpcClient,
    ):
        """Email is read from the stored column, not gRPC."""
        project = await _seed_project(db, user_alice)

        result = await member_service.list_members(
            db,
            grpc_client_mock,
            project_id=project.id,
        )

        assert len(result) == 1
        assert result[0].email == "alice@example.com"


# ── transfer_ownership ────────────────────────────────────────────────────────


class TestTransferOwnership:
    @pytest.mark.asyncio
    async def test_transfer_success(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
    ):
        project = await _seed_project(db, user_alice)
        await member_repo.add_member(
            db,
            project_id=project.id,
            user_id=user_bob.id,
            name=user_bob.name,
            email=user_bob.email,
        )
        await db.commit()

        await member_service.transfer_ownership(
            db,
            project_id=project.id,
            caller_id=user_alice.id,
            caller_name=user_alice.name,
            new_owner_id=user_bob.id,
        )

        # Verify roles are swapped
        alice_member = await member_repo.get(db, project.id, user_alice.id)
        bob_member = await member_repo.get(db, project.id, user_bob.id)
        assert alice_member.role == MemberRole.MEMBER
        assert bob_member.role == MemberRole.OWNER

        # Verify project.owner_id changed
        await db.refresh(project)
        assert project.owner_id == user_bob.id

    @pytest.mark.asyncio
    async def test_transfer_project_not_found(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
    ):
        with pytest.raises(ProjectNotFoundError):
            await member_service.transfer_ownership(
                db,
                project_id=uuid.uuid4(),
                caller_id=user_alice.id,
                caller_name=user_alice.name,
                new_owner_id=user_bob.id,
            )

    @pytest.mark.asyncio
    async def test_transfer_not_owner(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        user_charlie: CurrentUser,
    ):
        project = await _seed_project(db, user_alice)
        await member_repo.add_member(
            db,
            project_id=project.id,
            user_id=user_bob.id,
            name=user_bob.name,
            email=user_bob.email,
        )
        await db.commit()

        with pytest.raises(ForbiddenError, match="Owner only"):
            await member_service.transfer_ownership(
                db,
                project_id=project.id,
                caller_id=user_bob.id,
                caller_name=user_bob.name,
                new_owner_id=user_charlie.id,
            )

    @pytest.mark.asyncio
    async def test_transfer_self(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
    ):
        project = await _seed_project(db, user_alice)

        with pytest.raises(BadRequestError, match="already the owner"):
            await member_service.transfer_ownership(
                db,
                project_id=project.id,
                caller_id=user_alice.id,
                caller_name=user_alice.name,
                new_owner_id=user_alice.id,
            )

    @pytest.mark.asyncio
    async def test_transfer_target_not_member(
        self,
        db: AsyncSession,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
    ):
        project = await _seed_project(db, user_alice)

        with pytest.raises(BadRequestError, match="not a current member"):
            await member_service.transfer_ownership(
                db,
                project_id=project.id,
                caller_id=user_alice.id,
                caller_name=user_alice.name,
                new_owner_id=user_bob.id,
            )
