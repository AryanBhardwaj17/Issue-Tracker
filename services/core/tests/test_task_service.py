"""
Tests for the Task service — create, list, update, delete for tasks + subtasks.

Covers:
- Create task: basic, with assignee, assignee not member → 400, story not found → 404
- Create subtask: basic, depth guard → 400, parent not found → 404
- List tasks: grouped with subtasks, pagination, empty
- Update task: owner edits any, reporter edits own, member can't edit other's → 403,
  is_done assignee-or-owner rule
- Soft-delete task: reporter deletes own, owner deletes any, member can't delete
  other's → 403, cascade to subtasks
- List subtasks: paginated
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership
from app.core.exceptions import (
    BadRequestError,
    ForbiddenError,
    StoryNotFoundError,
    TaskNotFoundError,
)
from app.models.project_member import MemberRole
from app.models.story import Priority, StoryStatus, UserStory
from app.repositories import project as project_repo
from app.repositories import project_members as member_repo
from app.repositories import task as task_repo
from app.schemas.task import TaskCreateRequest, TaskUpdateRequest
from app.services import task as task_service

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def project(db: AsyncSession, user_alice: CurrentUser):
    """Create a project owned by Alice."""
    proj = await project_repo.create(
        db, name="Test Project", key="TEST", description=None, owner_id=user_alice.id
    )
    await member_repo.add_member(
        db,
        project_id=proj.id,
        user_id=user_alice.id,
        name="Alice",
        email="alice@example.com",
        role=MemberRole.OWNER,
    )
    await db.commit()
    return proj


@pytest_asyncio.fixture
async def bob_membership(db: AsyncSession, project, user_bob: CurrentUser):
    """Add Bob as a member of the project."""
    await member_repo.add_member(
        db,
        project_id=project.id,
        user_id=user_bob.id,
        name="Bob",
        email="bob@example.com",
        role=MemberRole.MEMBER,
    )
    await db.commit()
    return ProjectMembership(
        user_id=user_bob.id,
        project_id=project.id,
        name="Bob",
        role=MemberRole.MEMBER.value,
    )


@pytest_asyncio.fixture
async def alice_membership(project, user_alice: CurrentUser):
    """Alice's owner membership."""
    return ProjectMembership(
        user_id=user_alice.id,
        project_id=project.id,
        name="Alice",
        role=MemberRole.OWNER.value,
    )


@pytest_asyncio.fixture
async def story(db: AsyncSession, project):
    """Create a user story in the project."""
    s = UserStory(
        project_id=project.id,
        story_key="TEST-1",
        title="Test Story",
        description="A story for testing tasks",
        priority=Priority.MEDIUM,
        status=StoryStatus.TODO,
        reporter_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    )
    db.add(s)
    await db.flush()
    await db.refresh(s)
    await db.commit()
    return s


# ── Create Task ───────────────────────────────────────────────────────────────


class TestCreateTask:
    async def test_create_basic(self, db: AsyncSession, project, story, user_alice: CurrentUser):
        """Basic task creation with no assignee."""
        data = TaskCreateRequest(title="My Task", priority=Priority.HIGH)
        result = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_alice
        )
        assert result.title == "My Task"
        assert result.priority == "high"
        assert result.assignee is None
        assert result.reporter_id == user_alice.id
        assert result.is_done is False
        assert result.parent_id is None
        assert result.story_id == story.id

    async def test_create_with_assignee(
        self, db: AsyncSession, project, story, user_alice: CurrentUser, bob_membership
    ):
        """Task creation with a valid assignee."""
        data = TaskCreateRequest(
            title="Assigned Task", priority=Priority.LOW, assignee_id=bob_membership.user_id
        )
        result = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_alice
        )
        assert result.assignee is not None
        assert result.assignee.id == bob_membership.user_id
        assert result.assignee.name == "Bob"

    async def test_create_assignee_not_member(
        self, db: AsyncSession, project, story, user_alice: CurrentUser
    ):
        """Assigning to a non-member raises 400."""
        non_member_id = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
        data = TaskCreateRequest(
            title="Bad Task", priority=Priority.MEDIUM, assignee_id=non_member_id
        )
        with pytest.raises(BadRequestError, match="Assignee must be a project member"):
            await task_service.create_task(
                db, story_id=story.id, project_id=project.id, data=data, user=user_alice
            )

    async def test_create_story_not_found(self, db: AsyncSession, project, user_alice: CurrentUser):
        """Creating a task for a non-existent story raises 404."""
        fake_story_id = uuid.uuid4()
        data = TaskCreateRequest(title="Orphan Task", priority=Priority.LOW)
        with pytest.raises(StoryNotFoundError):
            await task_service.create_task(
                db, story_id=fake_story_id, project_id=project.id, data=data, user=user_alice
            )

    async def test_create_story_wrong_project(
        self, db: AsyncSession, project, story, user_alice: CurrentUser
    ):
        """Creating a task where story belongs to a different project raises 404."""
        other_project_id = uuid.uuid4()
        data = TaskCreateRequest(title="Wrong Project Task", priority=Priority.LOW)
        with pytest.raises(StoryNotFoundError):
            await task_service.create_task(
                db, story_id=story.id, project_id=other_project_id, data=data, user=user_alice
            )


# ── Create Subtask ────────────────────────────────────────────────────────────


class TestCreateSubtask:
    @pytest_asyncio.fixture
    async def parent_task(self, db: AsyncSession, project, story, user_alice: CurrentUser):
        """Create a parent task for subtask tests."""
        data = TaskCreateRequest(title="Parent Task", priority=Priority.HIGH)
        result = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_alice
        )
        return result

    async def test_create_basic(
        self, db: AsyncSession, project, story, parent_task, user_alice: CurrentUser
    ):
        """Basic subtask creation."""
        data = TaskCreateRequest(title="My Subtask", priority=Priority.LOW)
        result = await task_service.create_subtask(
            db, parent_task_id=parent_task.id, project_id=project.id, data=data, user=user_alice
        )
        assert result.title == "My Subtask"
        assert result.parent_id == parent_task.id
        assert result.reporter_id == user_alice.id
        assert result.is_done is False

    async def test_depth_guard(
        self, db: AsyncSession, project, story, parent_task, user_alice: CurrentUser
    ):
        """Creating a subtask under a subtask raises 400."""
        # First, create a subtask
        data = TaskCreateRequest(title="Subtask", priority=Priority.LOW)
        subtask = await task_service.create_subtask(
            db, parent_task_id=parent_task.id, project_id=project.id, data=data, user=user_alice
        )
        # Try to create a subtask under the subtask
        data2 = TaskCreateRequest(title="Sub-subtask", priority=Priority.LOW)
        with pytest.raises(BadRequestError, match="Cannot create a subtask under another subtask"):
            await task_service.create_subtask(
                db, parent_task_id=subtask.id, project_id=project.id, data=data2, user=user_alice
            )

    async def test_parent_not_found(self, db: AsyncSession, project, user_alice: CurrentUser):
        """Creating a subtask with non-existent parent raises 404."""
        fake_id = uuid.uuid4()
        data = TaskCreateRequest(title="Orphan Subtask", priority=Priority.LOW)
        with pytest.raises(TaskNotFoundError):
            await task_service.create_subtask(
                db, parent_task_id=fake_id, project_id=project.id, data=data, user=user_alice
            )

    async def test_parent_wrong_project(
        self, db: AsyncSession, project, story, parent_task, user_alice: CurrentUser
    ):
        """Creating a subtask where parent belongs to a different project raises 404."""
        other_project_id = uuid.uuid4()
        data = TaskCreateRequest(title="Wrong Project Subtask", priority=Priority.LOW)
        with pytest.raises(TaskNotFoundError):
            await task_service.create_subtask(
                db,
                parent_task_id=parent_task.id,
                project_id=other_project_id,
                data=data,
                user=user_alice,
            )

    async def test_subtask_inherits_story_id(
        self, db: AsyncSession, project, story, parent_task, user_alice: CurrentUser
    ):
        """Subtask inherits story_id from parent."""
        data = TaskCreateRequest(title="Inherited Story", priority=Priority.MEDIUM)
        result = await task_service.create_subtask(
            db, parent_task_id=parent_task.id, project_id=project.id, data=data, user=user_alice
        )
        # Verify in DB
        db_task = await task_repo.get_by_id(db, result.id)
        assert db_task.story_id == story.id


# ── List Tasks ────────────────────────────────────────────────────────────────


class TestListTasks:
    async def test_list_with_subtasks_grouped(
        self, db: AsyncSession, project, story, user_alice: CurrentUser
    ):
        """Tasks listed with subtasks nested under their parent."""
        # Create 2 tasks
        data1 = TaskCreateRequest(title="Task 1", priority=Priority.HIGH)
        t1 = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data1, user=user_alice
        )
        data2 = TaskCreateRequest(title="Task 2", priority=Priority.LOW)
        await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data2, user=user_alice
        )
        # Create subtask under task 1
        sub_data = TaskCreateRequest(title="Sub 1", priority=Priority.MEDIUM)
        await task_service.create_subtask(
            db, parent_task_id=t1.id, project_id=project.id, data=sub_data, user=user_alice
        )

        tasks, pagination = await task_service.list_tasks_for_story(
            db, story_id=story.id, project_id=project.id, page=1, page_size=25
        )
        assert pagination.total == 2  # 2 top-level tasks
        assert len(tasks) == 2
        # First task has 1 subtask
        task1 = next(t for t in tasks if t.title == "Task 1")
        assert len(task1.subtasks) == 1
        assert task1.subtasks[0].title == "Sub 1"

    async def test_list_pagination(self, db: AsyncSession, project, story, user_alice: CurrentUser):
        """Pagination works at the parent-task level."""
        # Create 3 tasks
        for i in range(3):
            data = TaskCreateRequest(title=f"Task {i}", priority=Priority.LOW)
            await task_service.create_task(
                db, story_id=story.id, project_id=project.id, data=data, user=user_alice
            )

        tasks, pagination = await task_service.list_tasks_for_story(
            db, story_id=story.id, project_id=project.id, page=1, page_size=2
        )
        assert pagination.total == 3
        assert pagination.total_pages == 2
        assert len(tasks) == 2

    async def test_list_empty(self, db: AsyncSession, project, story, user_alice: CurrentUser):
        """Empty story returns empty list."""
        tasks, pagination = await task_service.list_tasks_for_story(
            db, story_id=story.id, project_id=project.id, page=1, page_size=25
        )
        assert tasks == []
        assert pagination.total == 0

    async def test_list_story_not_found(self, db: AsyncSession, project, user_alice: CurrentUser):
        """Listing tasks for non-existent story raises 404."""
        fake_story_id = uuid.uuid4()
        with pytest.raises(StoryNotFoundError):
            await task_service.list_tasks_for_story(
                db, story_id=fake_story_id, project_id=project.id, page=1, page_size=25
            )

    async def test_deleted_tasks_excluded(
        self, db: AsyncSession, project, story, user_alice: CurrentUser, alice_membership
    ):
        """Soft-deleted tasks are excluded from listing."""
        data = TaskCreateRequest(title="To Delete", priority=Priority.HIGH)
        t = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_alice
        )
        await task_service.soft_delete_task(
            db, task_id=t.id, project_id=project.id, user=user_alice, membership=alice_membership
        )
        tasks, pagination = await task_service.list_tasks_for_story(
            db, story_id=story.id, project_id=project.id, page=1, page_size=25
        )
        assert tasks == []
        assert pagination.total == 0


# ── Update Task ───────────────────────────────────────────────────────────────


class TestUpdateTask:
    async def test_owner_can_update_any_task(
        self,
        db: AsyncSession,
        project,
        story,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        bob_membership,
        alice_membership,
    ):
        """Owner (Alice) can update a task created by another member (Bob)."""
        # Bob creates a task
        data = TaskCreateRequest(title="Bob's Task", priority=Priority.LOW)
        t = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_bob
        )
        # Alice (owner) updates it
        update_data = TaskUpdateRequest(title="Updated by Alice")
        result = await task_service.update_task(
            db,
            task_id=t.id,
            project_id=project.id,
            data=update_data,
            user=user_alice,
            membership=alice_membership,
        )
        assert result.title == "Updated by Alice"

    async def test_reporter_can_update_own_task(
        self, db: AsyncSession, project, story, user_bob: CurrentUser, bob_membership
    ):
        """Reporter (Bob) can update their own task."""
        data = TaskCreateRequest(title="Bob's Task", priority=Priority.LOW)
        t = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_bob
        )
        update_data = TaskUpdateRequest(title="Updated by Bob")
        result = await task_service.update_task(
            db,
            task_id=t.id,
            project_id=project.id,
            data=update_data,
            user=user_bob,
            membership=bob_membership,
        )
        assert result.title == "Updated by Bob"

    async def test_member_cannot_update_others_task(
        self,
        db: AsyncSession,
        project,
        story,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        bob_membership,
    ):
        """Member (Bob) cannot update a task created by another member (Alice)."""
        # Alice creates a task
        data = TaskCreateRequest(title="Alice's Task", priority=Priority.HIGH)
        t = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_alice
        )
        # Bob tries to update it
        update_data = TaskUpdateRequest(title="Hacked by Bob")
        with pytest.raises(ForbiddenError, match="Only the reporter or Owner can edit"):
            await task_service.update_task(
                db,
                task_id=t.id,
                project_id=project.id,
                data=update_data,
                user=user_bob,
                membership=bob_membership,
            )

    async def test_is_done_toggle_assignee_rule(
        self,
        db: AsyncSession,
        project,
        story,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        bob_membership,
    ):
        """Only assignee or owner can toggle is_done when task has an assignee."""
        # Alice creates a task assigned to Alice
        data = TaskCreateRequest(
            title="Assigned to Alice", priority=Priority.LOW, assignee_id=user_alice.id
        )
        t = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_bob
        )
        # Bob (reporter but NOT assignee) tries to toggle is_done
        update_data = TaskUpdateRequest(is_done=True)
        with pytest.raises(ForbiddenError, match="Only the assignee or Owner can toggle"):
            await task_service.update_task(
                db,
                task_id=t.id,
                project_id=project.id,
                data=update_data,
                user=user_bob,
                membership=bob_membership,
            )

    async def test_is_done_toggle_by_assignee(
        self,
        db: AsyncSession,
        project,
        story,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        bob_membership,
    ):
        """Assignee can toggle is_done on their assigned task."""
        # Alice creates a task assigned to Bob
        data = TaskCreateRequest(
            title="Assigned to Bob", priority=Priority.LOW, assignee_id=user_bob.id
        )
        t = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_bob
        )
        # Bob (reporter + assignee) toggles is_done
        update_data = TaskUpdateRequest(is_done=True)
        result = await task_service.update_task(
            db,
            task_id=t.id,
            project_id=project.id,
            data=update_data,
            user=user_bob,
            membership=bob_membership,
        )
        assert result.is_done is True

    async def test_is_done_toggle_by_owner(
        self,
        db: AsyncSession,
        project,
        story,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        bob_membership,
        alice_membership,
    ):
        """Owner can toggle is_done on any assigned task."""
        # Bob creates a task assigned to Bob
        data = TaskCreateRequest(
            title="Assigned to Bob", priority=Priority.LOW, assignee_id=user_bob.id
        )
        t = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_bob
        )
        # Alice (owner, NOT assignee) toggles is_done
        update_data = TaskUpdateRequest(is_done=True)
        result = await task_service.update_task(
            db,
            task_id=t.id,
            project_id=project.id,
            data=update_data,
            user=user_alice,
            membership=alice_membership,
        )
        assert result.is_done is True

    async def test_update_task_not_found(
        self, db: AsyncSession, project, user_alice: CurrentUser, alice_membership
    ):
        """Updating a non-existent task raises 404."""
        fake_id = uuid.uuid4()
        update_data = TaskUpdateRequest(title="Ghost")
        with pytest.raises(TaskNotFoundError):
            await task_service.update_task(
                db,
                task_id=fake_id,
                project_id=project.id,
                data=update_data,
                user=user_alice,
                membership=alice_membership,
            )


# ── Soft-delete Task ──────────────────────────────────────────────────────────


class TestSoftDeleteTask:
    async def test_reporter_can_delete_own_task(
        self, db: AsyncSession, project, story, user_bob: CurrentUser, bob_membership
    ):
        """Reporter (Bob) can delete their own task."""
        data = TaskCreateRequest(title="Bob's Task", priority=Priority.LOW)
        t = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_bob
        )
        await task_service.soft_delete_task(
            db, task_id=t.id, project_id=project.id, user=user_bob, membership=bob_membership
        )
        # Verify deleted
        deleted = await task_repo.get_by_id(db, t.id)
        assert deleted is None

    async def test_owner_can_delete_any_task(
        self,
        db: AsyncSession,
        project,
        story,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        bob_membership,
        alice_membership,
    ):
        """Owner (Alice) can delete a task created by Bob."""
        data = TaskCreateRequest(title="Bob's Task", priority=Priority.LOW)
        t = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_bob
        )
        await task_service.soft_delete_task(
            db, task_id=t.id, project_id=project.id, user=user_alice, membership=alice_membership
        )
        deleted = await task_repo.get_by_id(db, t.id)
        assert deleted is None

    async def test_member_cannot_delete_others_task(
        self,
        db: AsyncSession,
        project,
        story,
        user_alice: CurrentUser,
        user_bob: CurrentUser,
        bob_membership,
    ):
        """Member (Bob) cannot delete a task created by Alice."""
        data = TaskCreateRequest(title="Alice's Task", priority=Priority.HIGH)
        t = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_alice
        )
        with pytest.raises(ForbiddenError, match="Only the reporter or Owner can delete"):
            await task_service.soft_delete_task(
                db, task_id=t.id, project_id=project.id, user=user_bob, membership=bob_membership
            )

    async def test_cascade_to_subtasks(
        self, db: AsyncSession, project, story, user_alice: CurrentUser, alice_membership
    ):
        """Deleting a parent task cascades soft-delete to its subtasks."""
        # Create task with 2 subtasks
        data = TaskCreateRequest(title="Parent", priority=Priority.HIGH)
        parent = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_alice
        )
        sub_data = TaskCreateRequest(title="Sub 1", priority=Priority.LOW)
        s1 = await task_service.create_subtask(
            db, parent_task_id=parent.id, project_id=project.id, data=sub_data, user=user_alice
        )
        sub_data2 = TaskCreateRequest(title="Sub 2", priority=Priority.LOW)
        s2 = await task_service.create_subtask(
            db, parent_task_id=parent.id, project_id=project.id, data=sub_data2, user=user_alice
        )

        # Delete parent
        await task_service.soft_delete_task(
            db,
            task_id=parent.id,
            project_id=project.id,
            user=user_alice,
            membership=alice_membership,
        )

        # Both subtasks should be soft-deleted
        assert await task_repo.get_by_id(db, s1.id) is None
        assert await task_repo.get_by_id(db, s2.id) is None

    async def test_delete_task_not_found(
        self, db: AsyncSession, project, user_alice: CurrentUser, alice_membership
    ):
        """Deleting a non-existent task raises 404."""
        fake_id = uuid.uuid4()
        with pytest.raises(TaskNotFoundError):
            await task_service.soft_delete_task(
                db,
                task_id=fake_id,
                project_id=project.id,
                user=user_alice,
                membership=alice_membership,
            )


# ── List Subtasks ─────────────────────────────────────────────────────────────


class TestListSubtasks:
    async def test_list_subtasks(self, db: AsyncSession, project, story, user_alice: CurrentUser):
        """List subtasks of a given parent task."""
        # Create parent + 2 subtasks
        data = TaskCreateRequest(title="Parent", priority=Priority.HIGH)
        parent = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_alice
        )
        for i in range(2):
            sub_data = TaskCreateRequest(title=f"Sub {i}", priority=Priority.LOW)
            await task_service.create_subtask(
                db, parent_task_id=parent.id, project_id=project.id, data=sub_data, user=user_alice
            )

        subtasks, pagination = await task_service.list_subtasks(
            db, parent_task_id=parent.id, project_id=project.id, page=1, page_size=25
        )
        assert len(subtasks) == 2
        assert pagination.total == 2

    async def test_list_subtasks_parent_not_found(
        self, db: AsyncSession, project, user_alice: CurrentUser
    ):
        """Listing subtasks of non-existent parent raises 404."""
        fake_id = uuid.uuid4()
        with pytest.raises(TaskNotFoundError):
            await task_service.list_subtasks(
                db, parent_task_id=fake_id, project_id=project.id, page=1, page_size=25
            )


# ── Get Task ──────────────────────────────────────────────────────────────────


class TestGetTask:
    async def test_get_task_with_subtasks(
        self, db: AsyncSession, project, story, user_alice: CurrentUser
    ):
        """Get a single task includes its subtasks."""
        data = TaskCreateRequest(title="Parent", priority=Priority.HIGH)
        parent = await task_service.create_task(
            db, story_id=story.id, project_id=project.id, data=data, user=user_alice
        )
        sub_data = TaskCreateRequest(title="Sub", priority=Priority.LOW)
        await task_service.create_subtask(
            db, parent_task_id=parent.id, project_id=project.id, data=sub_data, user=user_alice
        )

        result = await task_service.get_task(db, task_id=parent.id, project_id=project.id)
        assert result.title == "Parent"
        assert len(result.subtasks) == 1
        assert result.subtasks[0].title == "Sub"

    async def test_get_task_not_found(self, db: AsyncSession, project):
        """Getting a non-existent task raises 404."""
        fake_id = uuid.uuid4()
        with pytest.raises(TaskNotFoundError):
            await task_service.get_task(db, task_id=fake_id, project_id=project.id)
