"""
Task service — business logic for task and subtask CRUD.

Handles:
- create_task / create_subtask with depth guard
- list_tasks_for_story (paginated at parent level, subtasks nested)
- list_subtasks (paginated)
- get_task (single task with subtasks)
- update_task with permission + assignee-or-owner rule for is_done
- soft_delete_task with cascade to subtasks

Permission model (user's custom requirement):
- Members can only edit/delete tasks THEY created (reporter_id == caller).
- Owner has full access to edit/delete any task/subtask.
"""

import logging
import uuid
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership
from app.core.exceptions import (
    BadRequestError,
    ForbiddenError,
    StoryNotFoundError,
    TaskNotFoundError,
)
from app.models.project_member import MemberRole
from app.models.task import Task
from app.repositories import project_members as member_repo
from app.repositories import story as story_repo
from app.repositories import task as task_repo
from app.schemas.common import Pagination, paginate
from app.schemas.task import AssigneeOut, SubtaskOut, TaskCreateRequest, TaskOut, TaskUpdateRequest
from app.utils.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    ERR_ASSIGNEE_NOT_MEMBER,
    ERR_SUBTASK_DEPTH,
    ERR_TASK_DELETE_FORBIDDEN,
    ERR_TASK_DONE_FORBIDDEN,
    ERR_TASK_EDIT_FORBIDDEN,
    ERR_TASK_SUBTASKS_INCOMPLETE,
    MAX_PAGE_SIZE,
)

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _validate_assignee(
    db: AsyncSession, project_id: uuid.UUID, assignee_id: uuid.UUID
) -> None:
    """Raise 400 if the assignee is not a project member."""
    member = await member_repo.get(db, project_id, assignee_id)
    if member is None:
        logger.warning(
            "Assignee validation failed: user=%s not a member of project=%s",
            assignee_id, project_id,
        )
        raise BadRequestError(ERR_ASSIGNEE_NOT_MEMBER)


async def _build_assignee_map(
    db: AsyncSession, project_id: uuid.UUID, tasks: list[Task]
) -> dict[uuid.UUID, AssigneeOut]:
    """Resolve assignee names for a batch of tasks via project_members."""
    assignee_ids = {t.assignee_id for t in tasks if t.assignee_id is not None}
    if not assignee_ids:
        return {}

    members = await member_repo.list_members(db, project_id)
    return {
        m.user_id: AssigneeOut(id=m.user_id, name=m.name)
        for m in members
        if m.user_id in assignee_ids
    }


def _task_to_subtask_out(task: Task, assignee_map: dict[uuid.UUID, AssigneeOut]) -> SubtaskOut:
    """Map an ORM Task (subtask) to SubtaskOut."""
    return SubtaskOut(
        id=task.id,
        parent_id=task.parent_id,
        title=task.title,
        description=task.description,
        priority=task.priority.value if hasattr(task.priority, "value") else task.priority,
        assignee=assignee_map.get(task.assignee_id) if task.assignee_id else None,
        reporter_id=task.reporter_id,
        due_date=task.due_date,
        is_done=task.is_done,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _task_to_out(
    task: Task,
    subtasks: list[Task],
    assignee_map: dict[uuid.UUID, AssigneeOut],
) -> TaskOut:
    """Map an ORM Task (parent) to TaskOut with nested subtasks."""
    return TaskOut(
        id=task.id,
        story_id=task.story_id,
        parent_id=task.parent_id,
        title=task.title,
        description=task.description,
        priority=task.priority.value if hasattr(task.priority, "value") else task.priority,
        assignee=assignee_map.get(task.assignee_id) if task.assignee_id else None,
        reporter_id=task.reporter_id,
        due_date=task.due_date,
        is_done=task.is_done,
        created_at=task.created_at,
        updated_at=task.updated_at,
        subtasks=[_task_to_subtask_out(st, assignee_map) for st in subtasks],
    )


# ── Create task ───────────────────────────────────────────────────────────────


async def create_task(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    project_id: uuid.UUID,
    data: TaskCreateRequest,
    user: CurrentUser,
) -> TaskOut:
    """
    Create a top-level task under a story.

    Validates:
    - Story exists and belongs to this project.
    - Assignee (if provided) is a project member.
    """
    story = await story_repo.get_by_id(db, story_id)
    if story is None or story.project_id != project_id:
        logger.warning("Task create failed: story=%s not found in project=%s", story_id, project_id)
        raise StoryNotFoundError()

    if data.assignee_id is not None:
        await _validate_assignee(db, project_id, data.assignee_id)

    task = await task_repo.create(
        db,
        project_id=project_id,
        story_id=story_id,
        parent_id=None,
        title=data.title,
        description=data.description,
        priority=data.priority.value,
        assignee_id=data.assignee_id,
        reporter_id=user.id,
        due_date=data.due_date,
    )
    await db.commit()
    await db.refresh(task)

    assignee_map = await _build_assignee_map(db, project_id, [task])
    logger.info("Task created: id=%s story=%s by=%s", task.id, story_id, user.id)
    return _task_to_out(task, [], assignee_map)


# ── Create subtask ────────────────────────────────────────────────────────────


async def create_subtask(
    db: AsyncSession,
    *,
    parent_task_id: uuid.UUID,
    project_id: uuid.UUID,
    data: TaskCreateRequest,
    user: CurrentUser,
) -> SubtaskOut:
    """
    Create a subtask under a parent task.

    Validates:
    - Parent task exists and belongs to project.
    - Depth guard: parent must not itself be a subtask.
    - Assignee (if provided) is a project member.
    """
    parent = await task_repo.get_by_id(db, parent_task_id)
    if parent is None or parent.project_id != project_id:
        logger.warning(
            "Subtask create failed: parent=%s not found in project=%s",
            parent_task_id, project_id,
        )
        raise TaskNotFoundError()

    # Depth guard — parent must be a top-level task
    if parent.parent_id is not None:
        logger.warning("Depth guard triggered: parent=%s is already a subtask", parent_task_id)
        raise BadRequestError(ERR_SUBTASK_DEPTH)

    if data.assignee_id is not None:
        await _validate_assignee(db, project_id, data.assignee_id)

    subtask = await task_repo.create(
        db,
        project_id=project_id,
        story_id=parent.story_id,
        parent_id=parent.id,
        title=data.title,
        description=data.description,
        priority=data.priority.value,
        assignee_id=data.assignee_id,
        reporter_id=user.id,
        due_date=data.due_date,
    )
    await db.commit()
    await db.refresh(subtask)

    assignee_map = await _build_assignee_map(db, project_id, [subtask])
    logger.info("Subtask created: id=%s parent=%s by=%s", subtask.id, parent_task_id, user.id)
    return _task_to_subtask_out(subtask, assignee_map)


# ── List tasks for story ──────────────────────────────────────────────────────


async def list_tasks_for_story(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[TaskOut], Pagination]:
    """
    List top-level tasks for a story with subtasks nested under each.
    Paginated at the parent-task level.
    """
    story = await story_repo.get_by_id(db, story_id)
    if story is None or story.project_id != project_id:
        raise StoryNotFoundError()

    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    # Get paginated top-level tasks
    total = await task_repo.count_top_level_for_story(db, story_id)
    top_tasks = await task_repo.list_top_level_for_story(db, story_id, offset, page_size)

    if not top_tasks:
        return [], paginate(page, page_size, total)

    # Get all non-deleted rows for story in one query to group subtasks
    all_tasks = await task_repo.list_for_story(db, story_id)

    # Group subtasks by parent_id
    subtask_map: dict[uuid.UUID, list[Task]] = defaultdict(list)
    for t in all_tasks:
        if t.parent_id is not None:
            subtask_map[t.parent_id].append(t)

    # Build assignee map for all tasks
    assignee_map = await _build_assignee_map(db, project_id, all_tasks)

    result = [
        _task_to_out(task, subtask_map.get(task.id, []), assignee_map)
        for task in top_tasks
    ]
    logger.debug(
        "Listed tasks: story=%s page=%d total=%d returned=%d",
        story_id, page, total, len(result),
    )
    return result, paginate(page, page_size, total)


# ── List subtasks ─────────────────────────────────────────────────────────────


async def list_subtasks(
    db: AsyncSession,
    *,
    parent_task_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[SubtaskOut], Pagination]:
    """List subtasks of a given parent task, paginated."""
    parent = await task_repo.get_by_id(db, parent_task_id)
    if parent is None or parent.project_id != project_id:
        raise TaskNotFoundError()

    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)

    total = await task_repo.count_subtasks(db, parent_task_id)
    subtasks = await task_repo.list_subtasks(db, parent_task_id)

    # Manual pagination on the already-fetched list (list is small)
    offset = (page - 1) * page_size
    page_items = subtasks[offset : offset + page_size]

    assignee_map = await _build_assignee_map(db, project_id, page_items)
    result = [_task_to_subtask_out(st, assignee_map) for st in page_items]
    return result, paginate(page, page_size, total)


# ── Get task ──────────────────────────────────────────────────────────────────


async def get_task(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
) -> TaskOut:
    """Get a single task with its subtasks."""
    task = await task_repo.get_by_id(db, task_id)
    if task is None or task.project_id != project_id:
        raise TaskNotFoundError()

    subtasks = await task_repo.list_subtasks(db, task_id) if task.parent_id is None else []
    all_items = [task] + subtasks
    assignee_map = await _build_assignee_map(db, project_id, all_items)
    return _task_to_out(task, subtasks, assignee_map)


# ── Update task ───────────────────────────────────────────────────────────────


async def update_task(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    data: TaskUpdateRequest,
    user: CurrentUser,
    membership: ProjectMembership,
) -> TaskOut:
    """
    Update a task/subtask.

    Permission:
    - reporter_id == caller.id → allowed (member edits own task)
    - membership.role == "owner" → allowed (owner edits any task)
    - Otherwise → 403

    is_done toggle rule (additional):
    - If the task has an assignee, only the assignee, reporter, or owner can toggle is_done.
    """
    task = await task_repo.get_by_id(db, task_id)
    if task is None or task.project_id != project_id:
        raise TaskNotFoundError()

    is_owner = membership.role == MemberRole.OWNER.value
    is_reporter = task.reporter_id == user.id

    # Also allow the story assignee to edit/toggle tasks
    story = await story_repo.get_by_id(db, task.story_id)
    is_story_assignee = story is not None and story.assignee_id == user.id

    # Permission: only reporter, story assignee, or owner can edit
    if not is_reporter and not is_story_assignee and not is_owner:
        logger.warning(
            "Task edit forbidden: user=%s is not reporter/story-assignee/owner of task=%s", user.id, task_id
        )
        raise ForbiddenError(ERR_TASK_EDIT_FORBIDDEN)

    # is_done toggle: story assignee, reporter, or owner rule
    if data.is_done is not None and story is not None and story.assignee_id is not None:
        if not is_story_assignee and not is_reporter and not is_owner:
            logger.warning(
                "is_done toggle forbidden: user=%s is not story-assignee/reporter/owner of task=%s",
                user.id, task_id,
            )
            raise ForbiddenError(ERR_TASK_DONE_FORBIDDEN)

    # is_done=True on root task: all subtasks must be done first
    if data.is_done is True and task.parent_id is None:
        subtasks_for_check = await task_repo.list_subtasks(db, task_id)
        if any(not s.is_done for s in subtasks_for_check):
            raise BadRequestError(ERR_TASK_SUBTASKS_INCOMPLETE)

    # Validate assignee change
    if data.assignee_id is not None:
        await _validate_assignee(db, project_id, data.assignee_id)

    # Build update values (only non-None fields)
    values: dict = {}
    if data.title is not None:
        values["title"] = data.title
    if data.description is not None:
        values["description"] = data.description
    if data.priority is not None:
        values["priority"] = data.priority.value
    if data.assignee_id is not None:
        values["assignee_id"] = data.assignee_id
    if data.due_date is not None:
        values["due_date"] = data.due_date
    if data.is_done is not None:
        values["is_done"] = data.is_done

    if values:
        await task_repo.update_fields(db, task_id, **values)
        await db.commit()
        await db.refresh(task)

    subtasks = await task_repo.list_subtasks(db, task_id) if task.parent_id is None else []
    all_items = [task] + subtasks
    assignee_map = await _build_assignee_map(db, project_id, all_items)

    logger.info("Task updated: id=%s by=%s", task_id, user.id)
    return _task_to_out(task, subtasks, assignee_map)


# ── Soft-delete task ──────────────────────────────────────────────────────────


async def soft_delete_task(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    user: CurrentUser,
    membership: ProjectMembership,
) -> None:
    """
    Soft-delete a task and cascade to its subtasks.

    Permission:
    - reporter_id == caller.id → allowed
    - membership.role == "owner" → allowed
    - Otherwise → 403
    """
    task = await task_repo.get_by_id(db, task_id)
    if task is None or task.project_id != project_id:
        raise TaskNotFoundError()

    is_owner = membership.role == MemberRole.OWNER.value
    is_reporter = task.reporter_id == user.id

    if not is_reporter and not is_owner:
        logger.warning(
            "Task delete forbidden: user=%s is not reporter/owner of task=%s", user.id, task_id
        )
        raise ForbiddenError(ERR_TASK_DELETE_FORBIDDEN)

    # Cascade: soft-delete subtasks first (if this is a parent task)
    if task.parent_id is None:
        await task_repo.soft_delete_subtasks(db, task_id)

    await task_repo.soft_delete(db, task_id)
    await db.commit()

    logger.info(
        "Task soft-deleted: id=%s (cascade=%s) by=%s", task_id, task.parent_id is None, user.id
    )
