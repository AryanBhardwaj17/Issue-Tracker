"""
Unit tests for pure functions in ``services.project``:
- ``extract_key_base``
- ``_next_unique_key`` (mocked DB)
- ``_to_project_out`` (mapping helper)
"""

import types
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import KeyGenerationError
from app.schemas.project import ProjectOut
from app.services.project import _next_unique_key, _to_project_out, extract_key_base

# ── extract_key_base ──────────────────────────────────────────────────────────


class TestExtractKeyBase:
    def test_simple_name(self):
        assert extract_key_base("Shop Front") == "SHOP"

    def test_two_letter_name(self):
        assert extract_key_base("Go!") == "GO"

    def test_single_letter(self):
        assert extract_key_base("X") == "X"

    def test_exactly_four_letters(self):
        assert extract_key_base("ABCD") == "ABCD"

    def test_more_than_four_letters_truncated(self):
        assert extract_key_base("LongProjectName") == "LONG"

    def test_leading_digits_stripped(self):
        # digits are stripped, letters remain
        assert extract_key_base("123Shop") == "SHOP"

    def test_mixed_case_uppercased(self):
        assert extract_key_base("myApp") == "MYAP"

    def test_unicode_stripped_leaves_ascii(self):
        # non-ASCII chars are stripped; ASCII letters kept
        assert extract_key_base("Ångström") == "NGST"

    def test_only_digits_raises(self):
        with pytest.raises(ValueError, match="at least one ASCII letter"):
            extract_key_base("123456")

    def test_only_symbols_raises(self):
        with pytest.raises(ValueError):
            extract_key_base("!@#$%")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            extract_key_base("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            extract_key_base("   ")

    def test_hyphen_separated_words(self):
        assert extract_key_base("e-commerce") == "ECOM"

    def test_numbers_interspersed(self):
        assert extract_key_base("a1b2c3d4e5") == "ABCD"


# ── _next_unique_key ──────────────────────────────────────────────────────────


class TestNextUniqueKey:
    @pytest.mark.asyncio
    async def test_returns_base_when_no_collision(self):
        mock_db = AsyncMock()
        with patch(
            "app.services.project.project_repo.get_by_key",
            new_callable=AsyncMock,
            return_value=None,
        ):
            key = await _next_unique_key(mock_db, "SHOP")
        assert key == "SHOP"

    @pytest.mark.asyncio
    async def test_increments_on_first_collision(self):
        mock_db = AsyncMock()
        # First call ("SHOP") returns a project (collision), second ("SHOP1") returns None
        side_effects = [object(), None]
        with patch(
            "app.services.project.project_repo.get_by_key",
            new_callable=AsyncMock,
            side_effect=side_effects,
        ):
            key = await _next_unique_key(mock_db, "SHOP")
        assert key == "SHOP1"

    @pytest.mark.asyncio
    async def test_increments_multiple_collisions(self):
        mock_db = AsyncMock()
        # SHOP, SHOP1, SHOP2 all collide; SHOP3 is free
        side_effects = [object(), object(), object(), None]
        with patch(
            "app.services.project.project_repo.get_by_key",
            new_callable=AsyncMock,
            side_effect=side_effects,
        ):
            key = await _next_unique_key(mock_db, "SHOP")
        assert key == "SHOP3"

    @pytest.mark.asyncio
    async def test_raises_key_generation_error_after_max_retries(self):
        mock_db = AsyncMock()
        # Always return a collision
        with patch(
            "app.services.project.project_repo.get_by_key",
            new_callable=AsyncMock,
            return_value=object(),
        ):
            with pytest.raises(KeyGenerationError):
                await _next_unique_key(mock_db, "SHOP")

    @pytest.mark.asyncio
    async def test_single_letter_base(self):
        mock_db = AsyncMock()
        with patch(
            "app.services.project.project_repo.get_by_key",
            new_callable=AsyncMock,
            return_value=None,
        ):
            key = await _next_unique_key(mock_db, "X")
        assert key == "X"


# ── _to_project_out ───────────────────────────────────────────────────────────


class TestToProjectOut:
    def _make_project(self, **kwargs) -> types.SimpleNamespace:
        now = datetime.now(UTC)
        defaults = dict(
            id=uuid.uuid4(),
            name="Test Project",
            key="TEST",
            description="A test project",
            owner_id=uuid.uuid4(),
            next_story_seq=0,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        defaults.update(kwargs)
        return types.SimpleNamespace(**defaults)

    def test_maps_all_fields(self):
        owner_id = uuid.uuid4()
        project = self._make_project(owner_id=owner_id)
        result = _to_project_out(project, "owner", 1, "Alice")

        assert isinstance(result, ProjectOut)
        assert result.id == project.id
        assert result.name == project.name
        assert result.key == project.key
        assert result.description == project.description
        assert result.owner.id == owner_id
        assert result.owner.name == "Alice"
        assert result.role == "owner"
        assert result.member_count == 1

    def test_member_role(self):
        project = self._make_project()
        result = _to_project_out(project, "member", 5, "Bob")
        assert result.role == "member"
        assert result.member_count == 5

    def test_none_description_preserved(self):
        project = self._make_project(description=None)
        result = _to_project_out(project, "owner", 1, "Alice")
        assert result.description is None

    def test_timestamps_preserved(self):
        now = datetime.now(UTC)
        project = self._make_project(created_at=now, updated_at=now)
        result = _to_project_out(project, "owner", 1, "Alice")
        assert result.created_at == now
        assert result.updated_at == now
