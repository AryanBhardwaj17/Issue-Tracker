"""
Unit tests for the epic service — guard logic and helper functions.

Uses mocks instead of a real database so tests are fast and isolated.
Covers: _to_epic_out helper, update_epic guards, delete_epic guards.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.deps import CurrentUser, ProjectMembership
from app.core.exceptions import (
    EpicDeleteForbiddenError,
    EpicEditForbiddenError,
    EpicNotFoundError,
)
from app.repositories.epic import EpicRow
from app.schemas.epic import EpicUpdate
from app.services.epic import _to_epic_out, create_epic, delete_epic, update_epic

# ── Constants ─────────────────────────────────────────────────────────────────

ALICE_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
BOB_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
PROJECT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
EPIC_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

# ── Factories ─────────────────────────────────────────────────────────────────


def _fake_epic(reporter_id: uuid.UUID) -> MagicMock:
    now = datetime.now(UTC)
    epic = MagicMock()
    epic.id = EPIC_ID
    epic.name = "Auth Flow"
    epic.description = "Some description"
    epic.reporter_id = reporter_id
    epic.created_at = now
    epic.updated_at = now
    return epic


def _epic_row(reporter_id: uuid.UUID) -> EpicRow:
    return EpicRow(epic=_fake_epic(reporter_id), total=3, done=1)


def _user(uid: uuid.UUID, name: str = "User") -> CurrentUser:
    return CurrentUser(id=uid, name=name, email=f"{name.lower()}@test.com")


def _membership(uid: uuid.UUID, role: str = "member") -> ProjectMembership:
    return ProjectMembership(user_id=uid, project_id=PROJECT_ID, name="User", role=role)


# ── _to_epic_out helper ───────────────────────────────────────────────────────


class TestToEpicOutHelper:
    def test_all_fields_mapped_correctly(self):
        now = datetime.now(UTC)
        epic = MagicMock()
        epic.id = EPIC_ID
        epic.name = "Test Epic"
        epic.description = "A description"
        epic.reporter_id = ALICE_ID
        epic.created_at = now
        epic.updated_at = now

        out = _to_epic_out(epic, reporter_name="Alice", total=5, done=2)

        assert out.id == EPIC_ID
        assert out.name == "Test Epic"
        assert out.description == "A description"
        assert out.reporter.id == ALICE_ID
        assert out.reporter.name == "Alice"
        assert out.progress.total == 5
        assert out.progress.done == 2

    def test_progress_defaults_to_zero(self):
        now = datetime.now(UTC)
        epic = MagicMock()
        epic.id = EPIC_ID
        epic.name = "Test"
        epic.description = None
        epic.reporter_id = ALICE_ID
        epic.created_at = now
        epic.updated_at = now

        out = _to_epic_out(epic, reporter_name="Alice")

        assert out.progress.total == 0
        assert out.progress.done == 0
        assert out.description is None

    def test_timestamps_preserved(self):
        fixed_time = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        epic = MagicMock()
        epic.id = EPIC_ID
        epic.name = "T"
        epic.description = None
        epic.reporter_id = ALICE_ID
        epic.created_at = fixed_time
        epic.updated_at = fixed_time

        out = _to_epic_out(epic, reporter_name="X")
        assert out.created_at == fixed_time
        assert out.updated_at == fixed_time


# ── update_epic guards ────────────────────────────────────────────────────────


class TestUpdateEpicGuards:
    @pytest.mark.asyncio
    async def test_not_found_raises_epic_not_found_error(self):
        db = AsyncMock()
        with patch("app.services.epic.epic_repo") as mock_repo:
            mock_repo.get_with_progress = AsyncMock(return_value=None)

            with pytest.raises(EpicNotFoundError):
                await update_epic(
                    db,
                    epic_id=EPIC_ID,
                    membership=_membership(ALICE_ID, "member"),
                    user=_user(ALICE_ID),
                    data=EpicUpdate(name="New"),
                )

    @pytest.mark.asyncio
    async def test_non_reporter_member_raises_forbidden(self):
        db = AsyncMock()
        # Alice created the epic; Bob (plain member) tries to edit
        with patch("app.services.epic.epic_repo") as mock_repo:
            mock_repo.get_with_progress = AsyncMock(return_value=_epic_row(ALICE_ID))

            with pytest.raises(EpicEditForbiddenError):
                await update_epic(
                    db,
                    epic_id=EPIC_ID,
                    membership=_membership(BOB_ID, "member"),
                    user=_user(BOB_ID),
                    data=EpicUpdate(name="New"),
                )

    @pytest.mark.asyncio
    async def test_reporter_is_allowed(self):
        db = AsyncMock()
        with patch("app.services.epic.epic_repo") as mock_repo, patch(
            "app.services.epic.member_repo"
        ) as mock_mr:
            mock_repo.get_with_progress = AsyncMock(return_value=_epic_row(ALICE_ID))
            mock_repo.update_fields = AsyncMock()
            mock_member = MagicMock()
            mock_member.name = "Alice"
            mock_mr.get = AsyncMock(return_value=mock_member)

            result = await update_epic(
                db,
                epic_id=EPIC_ID,
                membership=_membership(ALICE_ID, "member"),  # alice is reporter
                user=_user(ALICE_ID, "Alice"),
                data=EpicUpdate(name="Updated"),
            )
        assert result is not None
        mock_repo.update_fields.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_owner_is_allowed_even_if_not_reporter(self):
        db = AsyncMock()
        # Alice created the epic; Bob is owner (not reporter)
        with patch("app.services.epic.epic_repo") as mock_repo, patch(
            "app.services.epic.member_repo"
        ) as mock_mr:
            mock_repo.get_with_progress = AsyncMock(return_value=_epic_row(ALICE_ID))
            mock_repo.update_fields = AsyncMock()
            mock_member = MagicMock()
            mock_member.name = "Alice"
            mock_mr.get = AsyncMock(return_value=mock_member)

            result = await update_epic(
                db,
                epic_id=EPIC_ID,
                membership=_membership(BOB_ID, "owner"),
                user=_user(BOB_ID, "Bob"),
                data=EpicUpdate(name="Updated"),
            )
        assert result is not None
        mock_repo.update_fields.assert_awaited_once()


# ── delete_epic guards ────────────────────────────────────────────────────────


class TestDeleteEpicGuards:
    @pytest.mark.asyncio
    async def test_not_found_raises_epic_not_found_error(self):
        db = AsyncMock()
        with patch("app.services.epic.epic_repo") as mock_repo:
            mock_repo.get_with_progress = AsyncMock(return_value=None)

            with pytest.raises(EpicNotFoundError):
                await delete_epic(
                    db,
                    epic_id=EPIC_ID,
                    membership=_membership(ALICE_ID, "member"),
                    user=_user(ALICE_ID),
                )

    @pytest.mark.asyncio
    async def test_non_reporter_member_raises_forbidden(self):
        db = AsyncMock()
        with patch("app.services.epic.epic_repo") as mock_repo:
            mock_repo.get_with_progress = AsyncMock(return_value=_epic_row(ALICE_ID))

            with pytest.raises(EpicDeleteForbiddenError):
                await delete_epic(
                    db,
                    epic_id=EPIC_ID,
                    membership=_membership(BOB_ID, "member"),
                    user=_user(BOB_ID),
                )

    @pytest.mark.asyncio
    async def test_reporter_can_delete(self):
        db = AsyncMock()
        with patch("app.services.epic.epic_repo") as mock_repo:
            mock_repo.get_with_progress = AsyncMock(return_value=_epic_row(ALICE_ID))
            mock_repo.cascade_soft_delete = AsyncMock()

            await delete_epic(
                db,
                epic_id=EPIC_ID,
                membership=_membership(ALICE_ID, "member"),
                user=_user(ALICE_ID),
            )

        mock_repo.cascade_soft_delete.assert_awaited_once_with(db, EPIC_ID)

    @pytest.mark.asyncio
    async def test_owner_can_delete_any_epic(self):
        db = AsyncMock()
        # Alice created it; Bob is owner
        with patch("app.services.epic.epic_repo") as mock_repo:
            mock_repo.get_with_progress = AsyncMock(return_value=_epic_row(ALICE_ID))
            mock_repo.cascade_soft_delete = AsyncMock()

            await delete_epic(
                db,
                epic_id=EPIC_ID,
                membership=_membership(BOB_ID, "owner"),
                user=_user(BOB_ID),
            )

        mock_repo.cascade_soft_delete.assert_awaited_once_with(db, EPIC_ID)

    @pytest.mark.asyncio
    async def test_cascade_soft_delete_called_with_correct_id(self):
        db = AsyncMock()
        other_epic_id = uuid.uuid4()
        with patch("app.services.epic.epic_repo") as mock_repo:
            row = EpicRow(epic=_fake_epic(ALICE_ID), total=0, done=0)
            row.epic.id = other_epic_id
            mock_repo.get_with_progress = AsyncMock(return_value=row)
            mock_repo.cascade_soft_delete = AsyncMock()

            await delete_epic(
                db,
                epic_id=other_epic_id,
                membership=_membership(ALICE_ID, "member"),
                user=_user(ALICE_ID),
            )

        mock_repo.cascade_soft_delete.assert_awaited_once_with(db, other_epic_id)


# ── create_epic delegation ────────────────────────────────────────────────────


class TestCreateEpicDelegation:
    @pytest.mark.asyncio
    async def test_create_calls_repo_with_correct_args(self):
        db = AsyncMock()
        membership = _membership(ALICE_ID, "member")
        user = _user(ALICE_ID, "Alice")
        fake_epic = _fake_epic(ALICE_ID)

        with patch("app.services.epic.epic_repo") as mock_repo:
            mock_repo.create = AsyncMock(return_value=fake_epic)

            result = await create_epic(
                db, membership=membership, user=user, name="My Epic", description="Details"
            )

        mock_repo.create.assert_awaited_once_with(
            db,
            project_id=PROJECT_ID,
            name="My Epic",
            description="Details",
            reporter_id=ALICE_ID,
        )
        assert result.reporter.name == "Alice"
