"""
Integration tests for Project CRUD using a real in-process SQLite DB.

Tests exercise the full repo + service stack (no mocks) against the
``db`` fixture from conftest.py.
"""

import uuid

import pytest

from app.core.exceptions import ForbiddenError, KeyGenerationError, ProjectNotFoundError
from app.models.project_member import MemberRole
from app.repositories import project as project_repo
from app.repositories import project_members as member_repo
from app.services import project as project_service


# ── helpers ───────────────────────────────────────────────────────────────────


async def _create(db, user, name="My Project", description=None):
    return await project_service.create_project(
        db, user=user, name=name, description=description
    )


# ── create_project ────────────────────────────────────────────────────────────


class TestCreateProject:
    @pytest.mark.asyncio
    async def test_creates_project_and_returns_out(self, db, user_alice):
        out = await _create(db, user_alice, name="Shop Front")
        assert out.key == "SHOP"
        assert out.name == "Shop Front"
        assert out.role == MemberRole.OWNER.value
        assert out.member_count == 1

    @pytest.mark.asyncio
    async def test_owner_is_set_correctly(self, db, user_alice):
        out = await _create(db, user_alice)
        assert out.owner.id == user_alice.id
        assert out.owner.name == user_alice.name

    @pytest.mark.asyncio
    async def test_description_stored(self, db, user_alice):
        out = await _create(db, user_alice, description="My desc")
        assert out.description == "My desc"

    @pytest.mark.asyncio
    async def test_null_description_stored(self, db, user_alice):
        out = await _create(db, user_alice, description=None)
        assert out.description is None

    @pytest.mark.asyncio
    async def test_second_project_same_name_gets_suffix(self, db, user_alice, user_bob):
        out1 = await _create(db, user_alice, name="Shop Front")
        out2 = await _create(db, user_bob, name="Shop Front")
        assert out1.key == "SHOP"
        assert out2.key == "SHOP1"

    @pytest.mark.asyncio
    async def test_five_concurrent_same_name(self, db, user_alice):
        """Five sequential creates with the same name produce distinct keys."""
        keys = []
        for i in range(5):
            # reuse same user — each create adds the user as owner of a new project
            u = type(user_alice)(
                id=uuid.uuid4(), name=f"User{i}", email=f"u{i}@test.com"
            )
            out = await _create(db, u, name="Shop Front")
            keys.append(out.key)
        assert len(set(keys)) == 5
        assert keys[0] == "SHOP"
        assert keys[1] == "SHOP1"

    @pytest.mark.asyncio
    async def test_project_id_is_uuid(self, db, user_alice):
        out = await _create(db, user_alice)
        assert isinstance(out.id, uuid.UUID)


# ── get_project ───────────────────────────────────────────────────────────────


class TestGetProject:
    @pytest.mark.asyncio
    async def test_owner_can_get_project(self, db, user_alice):
        created = await _create(db, user_alice)
        fetched = await project_service.get_project(db, project_id=created.id, user=user_alice)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_non_member_gets_not_found(self, db, user_alice, user_bob):
        created = await _create(db, user_alice)
        with pytest.raises(ProjectNotFoundError):
            await project_service.get_project(db, project_id=created.id, user=user_bob)

    @pytest.mark.asyncio
    async def test_nonexistent_project_raises_not_found(self, db, user_alice):
        with pytest.raises(ProjectNotFoundError):
            await project_service.get_project(
                db, project_id=uuid.uuid4(), user=user_alice
            )


# ── list_projects ─────────────────────────────────────────────────────────────


class TestListProjects:
    @pytest.mark.asyncio
    async def test_returns_only_caller_projects(self, db, user_alice, user_bob):
        await _create(db, user_alice, name="Alice Project")
        await _create(db, user_bob, name="Bob Project")

        items, pagination = await project_service.list_projects(db, user=user_alice)
        assert len(items) == 1
        assert items[0].name == "Alice Project"

    @pytest.mark.asyncio
    async def test_pagination_total_correct(self, db, user_alice):
        for i in range(5):
            u = type(user_alice)(id=uuid.uuid4(), name=f"U{i}", email=f"u{i}@t.com")
            await _create(db, u, name=f"Project {i}")
        # alice has 0 projects of her own
        items, pagination = await project_service.list_projects(db, user=user_alice)
        assert pagination.total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_pagination_page_size_respected(self, db, user_alice):
        for i in range(5):
            await _create(db, user_alice, name=f"Proj {chr(65+i)}")
        items, pagination = await project_service.list_projects(
            db, user=user_alice, page=1, page_size=2
        )
        assert len(items) == 2
        assert pagination.total == 5
        assert pagination.total_pages == 3

    @pytest.mark.asyncio
    async def test_page_beyond_last_returns_empty(self, db, user_alice):
        await _create(db, user_alice, name="Only One")
        items, pagination = await project_service.list_projects(
            db, user=user_alice, page=99, page_size=25
        )
        assert items == []
        assert pagination.total == 1


# ── update_project ────────────────────────────────────────────────────────────


class TestUpdateProject:
    def _membership(self, user, project_id, role="owner"):
        from app.schemas.project import ProjectUpdateRequest
        return type("ProjectMembership", (), {
            "user_id": user.id,
            "project_id": project_id,
            "role": role,
            "name": user.name,
        })()

    @pytest.mark.asyncio
    async def test_owner_can_update_name(self, db, user_alice):
        from app.schemas.project import ProjectUpdateRequest
        created = await _create(db, user_alice)
        membership = self._membership(user_alice, created.id)
        updated = await project_service.update_project(
            db,
            project_id=created.id,
            data=ProjectUpdateRequest(name="New Name"),
            membership=membership,
        )
        assert updated.name == "New Name"
        assert updated.key == created.key  # key is immutable

    @pytest.mark.asyncio
    async def test_update_description_only(self, db, user_alice):
        from app.schemas.project import ProjectUpdateRequest
        created = await _create(db, user_alice, description="old")
        membership = self._membership(user_alice, created.id)
        updated = await project_service.update_project(
            db,
            project_id=created.id,
            data=ProjectUpdateRequest(description="new desc"),
            membership=membership,
        )
        assert updated.description == "new desc"
        assert updated.name == created.name  # name unchanged

    @pytest.mark.asyncio
    async def test_key_not_changed_by_name_update(self, db, user_alice):
        from app.schemas.project import ProjectUpdateRequest
        created = await _create(db, user_alice, name="Alpha")
        membership = self._membership(user_alice, created.id)
        updated = await project_service.update_project(
            db,
            project_id=created.id,
            data=ProjectUpdateRequest(name="Completely Different"),
            membership=membership,
        )
        assert updated.key == created.key  # key is locked to original


# ── soft_delete_project ───────────────────────────────────────────────────────


class TestSoftDeleteProject:
    @pytest.mark.asyncio
    async def test_deleted_project_not_in_list(self, db, user_alice):
        created = await _create(db, user_alice)
        await project_service.soft_delete_project(db, project_id=created.id)
        items, _ = await project_service.list_projects(db, user=user_alice)
        assert items == []

    @pytest.mark.asyncio
    async def test_deleted_project_get_raises_not_found(self, db, user_alice):
        created = await _create(db, user_alice)
        await project_service.soft_delete_project(db, project_id=created.id)
        with pytest.raises(ProjectNotFoundError):
            await project_service.get_project(db, project_id=created.id, user=user_alice)

    @pytest.mark.asyncio
    async def test_key_reusable_after_soft_delete(self, db, user_alice, user_bob):
        """
        The key uniqueness check uses get_by_key which includes soft-deleted rows,
        so a deleted project's key is still taken — the new project gets a suffix.
        """
        created = await _create(db, user_alice, name="Shop Front")
        await project_service.soft_delete_project(db, project_id=created.id)
        new = await _create(db, user_bob, name="Shop Front")
        assert new.key == "SHOP1"  # SHOP is still in DB (soft-deleted)


# ── deps: require_member / require_owner ──────────────────────────────────────


class TestMembershipChecks:
    @pytest.mark.asyncio
    async def test_require_member_raises_forbidden_for_non_member(self, db, user_alice, user_bob):
        created = await _create(db, user_alice)
        # Bob is not a member — member_repo.get returns None
        member = await member_repo.get(db, created.id, user_bob.id)
        assert member is None

    @pytest.mark.asyncio
    async def test_require_member_passes_for_owner(self, db, user_alice):
        created = await _create(db, user_alice)
        member = await member_repo.get(db, created.id, user_alice.id)
        assert member is not None
        assert member.role == MemberRole.OWNER

    @pytest.mark.asyncio
    async def test_owner_role_value(self, db, user_alice):
        created = await _create(db, user_alice)
        member = await member_repo.get(db, created.id, user_alice.id)
        assert member.role.value == "owner"
