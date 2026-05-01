"""
Integration tests for the Epic aggregate — repo + service layer against
an in-memory SQLite database.

Covers:
- Repository functions: create, get_by_id, count, list_with_progress,
  get_with_progress, update_fields, cascade_soft_delete
- Service functions: create_epic, list_epics, get_epic, update_epic,
  delete_epic (auth guards + cascade)
"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership
from app.core.exceptions import (
    EpicDeleteForbiddenError,
    EpicEditForbiddenError,
    EpicNotFoundError,
)
from app.models.project_member import MemberRole, ProjectMember
from app.models.story import Priority, StoryStatus, UserStory
from app.models.task import Task
from app.repositories import epic as epic_repo
from app.repositories import project as project_repo
from app.schemas.epic import EpicUpdate
from app.services import epic as epic_service

# ── Seed helpers ──────────────────────────────────────────────────────────────


async def _seed_project(db: AsyncSession, owner: CurrentUser, name: str = "Acme"):
    project = await project_repo.create(
        db, name=name, key=name[:4].upper(), description=None, owner_id=owner.id
    )
    await project_repo.add_owner_member(
        db, project_id=project.id, user_id=owner.id, name=owner.name, email=owner.email
    )
    await db.commit()
    return project


async def _add_member(db: AsyncSession, project_id: uuid.UUID, user: CurrentUser) -> None:
    db.add(
        ProjectMember(
            project_id=project_id,
            user_id=user.id,
            name=user.name,
            email=user.email,
            role=MemberRole.MEMBER,
        )
    )
    await db.commit()


async def _seed_epic(
    db: AsyncSession,
    project_id: uuid.UUID,
    reporter_id: uuid.UUID,
    name: str = "Epic A",
    description: str | None = "desc",
):
    epic = await epic_repo.create(
        db,
        project_id=project_id,
        name=name,
        description=description,
        reporter_id=reporter_id,
    )
    await db.commit()
    return epic


async def _seed_story(
    db: AsyncSession,
    project_id: uuid.UUID,
    epic_id: uuid.UUID | None,
    reporter_id: uuid.UUID,
    status: StoryStatus = StoryStatus.BACKLOG,
    key: str = "ACM-1",
) -> UserStory:
    story = UserStory(
        project_id=project_id,
        story_key=key,
        title="Story",
        status=status,
        priority=Priority.MEDIUM,
        reporter_id=reporter_id,
        epic_id=epic_id,
    )
    db.add(story)
    await db.commit()
    await db.refresh(story)
    return story


async def _seed_task(
    db: AsyncSession,
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    reporter_id: uuid.UUID,
) -> Task:
    task = Task(
        project_id=project_id,
        story_id=story_id,
        title="Task",
        priority=Priority.LOW,
        reporter_id=reporter_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


def _ms(project, user: CurrentUser, role: str = "member") -> ProjectMembership:
    return ProjectMembership(
        user_id=user.id, project_id=project.id, name=user.name, role=role
    )


# ── Epic repository ───────────────────────────────────────────────────────────


class TestEpicRepo:
    @pytest.mark.asyncio
    async def test_create_and_get_by_id(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)

        result = await epic_repo.get_by_id(db, epic.id)
        assert result is not None
        assert result.id == epic.id
        assert result.name == "Epic A"

    @pytest.mark.asyncio
    async def test_get_by_id_unknown_returns_none(self, db: AsyncSession, user_alice: CurrentUser):
        await _seed_project(db, user_alice)
        assert await epic_repo.get_by_id(db, uuid.uuid4()) is None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_soft_deleted(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)
        await epic_repo.cascade_soft_delete(db, epic.id)
        await db.commit()

        assert await epic_repo.get_by_id(db, epic.id) is None

    @pytest.mark.asyncio
    async def test_count_empty_project(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        assert await epic_repo.count_for_project(db, project.id) == 0

    @pytest.mark.asyncio
    async def test_count_excludes_soft_deleted(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)
        await epic_repo.cascade_soft_delete(db, epic.id)
        await db.commit()

        assert await epic_repo.count_for_project(db, project.id) == 0

    @pytest.mark.asyncio
    async def test_list_with_progress_returns_rows(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        await _seed_epic(db, project.id, user_alice.id, "E1")
        await _seed_epic(db, project.id, user_alice.id, "E2")

        rows = await epic_repo.list_with_progress(db, project.id, offset=0, limit=10)
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_get_with_progress_cross_project_returns_none(
        self, db: AsyncSession, user_alice: CurrentUser, user_bob: CurrentUser
    ):
        project1 = await _seed_project(db, user_alice, "Acme")
        project2 = await _seed_project(db, user_bob, "Beta")
        epic2 = await _seed_epic(db, project2.id, user_bob.id)

        assert await epic_repo.get_with_progress(db, epic2.id, project1.id) is None


# ── create_epic ───────────────────────────────────────────────────────────────


class TestCreateEpic:
    @pytest.mark.asyncio
    async def test_creates_epic_with_correct_fields(
        self, db: AsyncSession, user_alice: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        out = await epic_service.create_epic(
            db,
            membership=_ms(project, user_alice, "owner"),
            user=user_alice,
            name="Auth Flow",
            description=None,
        )
        assert out.name == "Auth Flow"
        assert out.reporter.id == user_alice.id
        assert out.reporter.name == user_alice.name

    @pytest.mark.asyncio
    async def test_progress_starts_at_zero(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        out = await epic_service.create_epic(
            db,
            membership=_ms(project, user_alice, "owner"),
            user=user_alice,
            name="E1",
            description=None,
        )
        assert out.progress.total == 0
        assert out.progress.done == 0

    @pytest.mark.asyncio
    async def test_description_stored(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        out = await epic_service.create_epic(
            db,
            membership=_ms(project, user_alice, "owner"),
            user=user_alice,
            name="E1",
            description="Has a description",
        )
        assert out.description == "Has a description"

    @pytest.mark.asyncio
    async def test_null_description(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        out = await epic_service.create_epic(
            db,
            membership=_ms(project, user_alice, "owner"),
            user=user_alice,
            name="E1",
            description=None,
        )
        assert out.description is None


# ── list_epics ────────────────────────────────────────────────────────────────


class TestListEpics:
    @pytest.mark.asyncio
    async def test_empty_project_returns_empty_list(
        self, db: AsyncSession, user_alice: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        items, pagination = await epic_service.list_epics(
            db, membership=_ms(project, user_alice, "owner")
        )
        assert items == []
        assert pagination.total == 0

    @pytest.mark.asyncio
    async def test_returns_all_epics(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        await _seed_epic(db, project.id, user_alice.id, "Epic A")
        await _seed_epic(db, project.id, user_alice.id, "Epic B")

        items, pagination = await epic_service.list_epics(
            db, membership=_ms(project, user_alice, "owner")
        )
        assert len(items) == 2
        assert pagination.total == 2

    @pytest.mark.asyncio
    async def test_soft_deleted_epics_excluded(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)
        await epic_repo.cascade_soft_delete(db, epic.id)
        await db.commit()

        items, pagination = await epic_service.list_epics(
            db, membership=_ms(project, user_alice, "owner")
        )
        assert items == []
        assert pagination.total == 0

    @pytest.mark.asyncio
    async def test_progress_counts_stories_correctly(
        self, db: AsyncSession, user_alice: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)
        await _seed_story(db, project.id, epic.id, user_alice.id, StoryStatus.BACKLOG, "ACM-1")
        await _seed_story(db, project.id, epic.id, user_alice.id, StoryStatus.DONE, "ACM-2")

        items, _ = await epic_service.list_epics(
            db, membership=_ms(project, user_alice, "owner")
        )
        assert items[0].progress.total == 2
        assert items[0].progress.done == 1

    @pytest.mark.asyncio
    async def test_soft_deleted_stories_excluded_from_progress(
        self, db: AsyncSession, user_alice: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)
        story = await _seed_story(db, project.id, epic.id, user_alice.id, key="ACM-1")
        story.is_deleted = True
        await db.commit()

        items, _ = await epic_service.list_epics(
            db, membership=_ms(project, user_alice, "owner")
        )
        assert items[0].progress.total == 0

    @pytest.mark.asyncio
    async def test_pagination_page_size_respected(
        self, db: AsyncSession, user_alice: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        for i in range(5):
            await _seed_epic(db, project.id, user_alice.id, f"Epic {i}")

        items, pagination = await epic_service.list_epics(
            db, membership=_ms(project, user_alice, "owner"), page=1, page_size=3
        )
        assert len(items) == 3
        assert pagination.total == 5
        assert pagination.total_pages == 2


# ── get_epic ──────────────────────────────────────────────────────────────────


class TestGetEpic:
    @pytest.mark.asyncio
    async def test_returns_epic_with_correct_fields(
        self, db: AsyncSession, user_alice: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)

        out = await epic_service.get_epic(
            db, epic_id=epic.id, membership=_ms(project, user_alice, "owner")
        )
        assert out.id == epic.id
        assert out.name == "Epic A"

    @pytest.mark.asyncio
    async def test_returns_progress(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)
        await _seed_story(db, project.id, epic.id, user_alice.id, StoryStatus.DONE, "ACM-1")

        out = await epic_service.get_epic(
            db, epic_id=epic.id, membership=_ms(project, user_alice, "owner")
        )
        assert out.progress.total == 1
        assert out.progress.done == 1

    @pytest.mark.asyncio
    async def test_raises_for_unknown_id(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        with pytest.raises(EpicNotFoundError):
            await epic_service.get_epic(
                db, epic_id=uuid.uuid4(), membership=_ms(project, user_alice, "owner")
            )

    @pytest.mark.asyncio
    async def test_raises_for_cross_project_access(
        self, db: AsyncSession, user_alice: CurrentUser, user_bob: CurrentUser
    ):
        project1 = await _seed_project(db, user_alice, "Acme")
        project2 = await _seed_project(db, user_bob, "Beta")
        epic2 = await _seed_epic(db, project2.id, user_bob.id)

        with pytest.raises(EpicNotFoundError):
            await epic_service.get_epic(
                db, epic_id=epic2.id, membership=_ms(project1, user_alice, "owner")
            )

    @pytest.mark.asyncio
    async def test_raises_for_soft_deleted_epic(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)
        await epic_repo.cascade_soft_delete(db, epic.id)
        await db.commit()

        with pytest.raises(EpicNotFoundError):
            await epic_service.get_epic(
                db, epic_id=epic.id, membership=_ms(project, user_alice, "owner")
            )


# ── update_epic ───────────────────────────────────────────────────────────────


class TestUpdateEpic:
    @pytest.mark.asyncio
    async def test_reporter_can_update_name(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)

        out = await epic_service.update_epic(
            db,
            epic_id=epic.id,
            membership=_ms(project, user_alice, "member"),
            user=user_alice,
            data=EpicUpdate(name="Renamed"),
        )
        assert out.name == "Renamed"

    @pytest.mark.asyncio
    async def test_owner_can_update_any_epic(
        self, db: AsyncSession, user_alice: CurrentUser, user_bob: CurrentUser
    ):
        project = await _seed_project(db, user_alice)  # alice is owner
        await _add_member(db, project.id, user_bob)
        epic = await _seed_epic(db, project.id, user_bob.id)  # bob created it

        out = await epic_service.update_epic(
            db,
            epic_id=epic.id,
            membership=_ms(project, user_alice, "owner"),
            user=user_alice,
            data=EpicUpdate(name="Owner Updated"),
        )
        assert out.name == "Owner Updated"

    @pytest.mark.asyncio
    async def test_other_member_raises_forbidden(
        self, db: AsyncSession, user_alice: CurrentUser, user_bob: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        await _add_member(db, project.id, user_bob)
        epic = await _seed_epic(db, project.id, user_alice.id)  # alice created it

        with pytest.raises(EpicEditForbiddenError):
            await epic_service.update_epic(
                db,
                epic_id=epic.id,
                membership=_ms(project, user_bob, "member"),  # bob is not reporter, not owner
                user=user_bob,
                data=EpicUpdate(name="Hijack"),
            )

    @pytest.mark.asyncio
    async def test_not_found_raises(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        with pytest.raises(EpicNotFoundError):
            await epic_service.update_epic(
                db,
                epic_id=uuid.uuid4(),
                membership=_ms(project, user_alice, "owner"),
                user=user_alice,
                data=EpicUpdate(name="X"),
            )

    @pytest.mark.asyncio
    async def test_partial_update_preserves_description(
        self, db: AsyncSession, user_alice: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        epic = await epic_repo.create(
            db,
            project_id=project.id,
            name="Original",
            description="Keep me",
            reporter_id=user_alice.id,
        )
        await db.commit()

        out = await epic_service.update_epic(
            db,
            epic_id=epic.id,
            membership=_ms(project, user_alice, "owner"),
            user=user_alice,
            data=EpicUpdate(name="New Name"),  # description omitted → None → not updated
        )
        assert out.name == "New Name"
        assert out.description == "Keep me"


# ── delete_epic ───────────────────────────────────────────────────────────────


class TestDeleteEpic:
    @pytest.mark.asyncio
    async def test_reporter_can_delete(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)

        await epic_service.delete_epic(
            db, epic_id=epic.id, membership=_ms(project, user_alice, "member"), user=user_alice
        )
        assert await epic_repo.get_by_id(db, epic.id) is None

    @pytest.mark.asyncio
    async def test_owner_can_delete_any_epic(
        self, db: AsyncSession, user_alice: CurrentUser, user_bob: CurrentUser
    ):
        project = await _seed_project(db, user_alice)  # alice is owner
        await _add_member(db, project.id, user_bob)
        epic = await _seed_epic(db, project.id, user_bob.id)  # bob created it

        await epic_service.delete_epic(
            db, epic_id=epic.id, membership=_ms(project, user_alice, "owner"), user=user_alice
        )
        assert await epic_repo.get_by_id(db, epic.id) is None

    @pytest.mark.asyncio
    async def test_other_member_raises_forbidden(
        self, db: AsyncSession, user_alice: CurrentUser, user_bob: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        await _add_member(db, project.id, user_bob)
        epic = await _seed_epic(db, project.id, user_alice.id)

        with pytest.raises(EpicDeleteForbiddenError):
            await epic_service.delete_epic(
                db, epic_id=epic.id, membership=_ms(project, user_bob, "member"), user=user_bob
            )

    @pytest.mark.asyncio
    async def test_not_found_raises(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        with pytest.raises(EpicNotFoundError):
            await epic_service.delete_epic(
                db,
                epic_id=uuid.uuid4(),
                membership=_ms(project, user_alice, "owner"),
                user=user_alice,
            )

    @pytest.mark.asyncio
    async def test_cascade_soft_deletes_stories(
        self, db: AsyncSession, user_alice: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)
        story = await _seed_story(db, project.id, epic.id, user_alice.id, key="ACM-1")

        await epic_service.delete_epic(
            db, epic_id=epic.id, membership=_ms(project, user_alice, "member"), user=user_alice
        )

        row = (await db.execute(select(UserStory).where(UserStory.id == story.id))).scalar_one()
        assert row.is_deleted is True

    @pytest.mark.asyncio
    async def test_cascade_soft_deletes_tasks(self, db: AsyncSession, user_alice: CurrentUser):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)
        story = await _seed_story(db, project.id, epic.id, user_alice.id, key="ACM-1")
        task = await _seed_task(db, project.id, story.id, user_alice.id)

        await epic_service.delete_epic(
            db, epic_id=epic.id, membership=_ms(project, user_alice, "member"), user=user_alice
        )

        row = (await db.execute(select(Task).where(Task.id == task.id))).scalar_one()
        assert row.is_deleted is True

    @pytest.mark.asyncio
    async def test_cascade_does_not_affect_unrelated_stories(
        self, db: AsyncSession, user_alice: CurrentUser
    ):
        project = await _seed_project(db, user_alice)
        epic = await _seed_epic(db, project.id, user_alice.id)
        unrelated = await _seed_story(
            db, project.id, None, user_alice.id, key="ACM-1"  # no epic_id
        )

        await epic_service.delete_epic(
            db, epic_id=epic.id, membership=_ms(project, user_alice, "member"), user=user_alice
        )

        row = (
            await db.execute(select(UserStory).where(UserStory.id == unrelated.id))
        ).scalar_one()
        assert row.is_deleted is False
