"""
Story service — business logic for the UserStory aggregate.

Responsibilities:
- Create, list, get, update, soft-delete stories.
- 7-status FSM transition enforcement.
- Atomic story-key generation (same transaction as insert).
- Assignee-is-member and epic-in-project guards.
- Domain event publishing stubs (story.assigned / story.unassigned).
- Soft-delete cascade to tasks and comments.
"""

import logging
import uuid

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership
from app.core.exceptions import BadRequestError, ForbiddenError, StoryNotFoundError, ValidationError
from app.events.constants import EVENT_STORY_ASSIGNED, EVENT_STORY_UNASSIGNED
from app.events.payloads import build_story_assigned_payload, build_story_unassigned_payload
from app.events.publisher import publish_event
from app.models.activity_log import ActivityAction, ActivityEntityType
from app.models.comment import Comment
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.story import Priority, StoryStatus, UserStory
from app.models.task import Task
from app.repositories import epic as epic_repo
from app.repositories import project_members as member_repo
from app.repositories import story as story_repo
from app.repositories import task as task_repo
from app.schemas.common import Pagination, paginate
from app.schemas.story import StoryCreate, StoryOut, StoryPatch, UserRef
from app.services.activity_log import log_activity
from app.utils.constants import (
    ALLOWED_SORT_FIELDS,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    ERR_ASSIGNEE_NOT_MEMBER,
    ERR_BACKLOG_REGRESSION,
    ERR_DELETE_FORBIDDEN,
    ERR_EPIC_NOT_IN_PROJECT,
    ERR_NO_FIELDS_TO_UPDATE,
    ERR_STATUS_CHANGE_FORBIDDEN,
    ERR_STORY_CREATE_STATUS,
    ERR_STORY_EDIT_FORBIDDEN,
    MAX_PAGE_SIZE,
    MAX_SEARCH_LENGTH,
)

logger = logging.getLogger(__name__)


# ── Status FSM ────────────────────────────────────────────────────────────────

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "backlog": {"todo"},
    "todo": {"todo", "in_progress", "in_review", "testing", "ready_for_prod", "done"},
    "in_progress": {"todo", "in_progress", "in_review", "testing", "ready_for_prod", "done"},
    "in_review": {"todo", "in_progress", "in_review", "testing", "ready_for_prod", "done"},
    "testing": {"todo", "in_progress", "in_review", "testing", "ready_for_prod", "done"},
    "ready_for_prod": {"todo", "in_progress", "in_review", "testing", "ready_for_prod", "done"},
    "done": {"todo", "in_progress", "in_review", "testing", "ready_for_prod", "done"},
}


def assert_transition_allowed(old: str, new: str) -> None:
    """Enforce the 7-status FSM. Same-status is always a no-op (idempotent)."""
    if old == new:
        return
    allowed = ALLOWED_TRANSITIONS.get(old, set())
    if new not in allowed:
        if new == "backlog":
            raise BadRequestError(ERR_BACKLOG_REGRESSION)
        raise BadRequestError(f"Cannot transition {old} → {new}")


# ── Guards ────────────────────────────────────────────────────────────────────


async def _assert_assignee_is_member(
    db: AsyncSession, project_id: uuid.UUID, assignee_id: uuid.UUID
) -> ProjectMember:
    """Raise 422 if the assignee is not a member of the project. Returns the member row."""
    member = await member_repo.get(db, project_id, assignee_id)
    if member is None:
        raise ValidationError(ERR_ASSIGNEE_NOT_MEMBER)
    return member


async def _assert_epic_in_project(
    db: AsyncSession, project_id: uuid.UUID, epic_id: uuid.UUID
) -> None:
    """Raise 400 if the epic doesn't exist, is deleted, or belongs to a different project."""
    epic = await epic_repo.get_by_id(db, epic_id)
    if epic is None or epic.project_id != project_id:
        raise BadRequestError(ERR_EPIC_NOT_IN_PROJECT)


def assert_can_delete(story: UserStory, user: CurrentUser, membership: ProjectMembership) -> None:
    """Only the reporter or the project owner can delete a story."""
    if story.reporter_id == user.id or membership.role == "owner":
        return
    raise ForbiddenError(ERR_DELETE_FORBIDDEN)


def assert_can_edit(story: UserStory, user: CurrentUser, membership: ProjectMembership) -> None:
    """Only the reporter, assignee, or the project owner can edit a story."""
    if membership.role == "owner":
        return
    if story.reporter_id == user.id:
        return
    if story.assignee_id is not None and story.assignee_id == user.id:
        return
    raise ForbiddenError(ERR_STORY_EDIT_FORBIDDEN)


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _resolve_user_ref(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> UserRef:
    """Look up a user's display name from project_members."""
    member = await member_repo.get(db, project_id, user_id)
    name = member.name if member else ""
    return UserRef(id=user_id, name=name)


async def _to_story_out(db: AsyncSession, story: UserStory, project_id: uuid.UUID) -> StoryOut:
    """Convert a UserStory ORM row to the response DTO with resolved names."""
    reporter = await _resolve_user_ref(db, project_id, story.reporter_id)
    assignee = None
    if story.assignee_id is not None:
        assignee = await _resolve_user_ref(db, project_id, story.assignee_id)

    return StoryOut(
        id=story.id,
        story_key=story.story_key,
        title=story.title,
        description=story.description,
        epic_id=story.epic_id,
        status=story.status.value if isinstance(story.status, StoryStatus) else story.status,
        priority=story.priority.value if isinstance(story.priority, Priority) else story.priority,
        story_points=story.story_points,
        assignee=assignee,
        reporter=reporter,
        due_date=story.due_date,
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


# ── Service functions ─────────────────────────────────────────────────────────


async def create_story(
    db: AsyncSession,
    *,
    project: Project,
    user: CurrentUser,
    body: StoryCreate,
) -> StoryOut:
    """Create a new story with atomic key generation."""
    # Status guard: only backlog or todo on create
    effective_status = body.status or "backlog"
    if effective_status not in ("backlog", "todo"):
        raise BadRequestError(ERR_STORY_CREATE_STATUS)

    # Assignee guard
    assignee_member: ProjectMember | None = None
    if body.assignee_id is not None:
        assignee_member = await _assert_assignee_is_member(db, project.id, body.assignee_id)

    # Epic guard
    if body.epic_id is not None:
        await _assert_epic_in_project(db, project.id, body.epic_id)

    # Atomic key generation (same transaction)
    key = await story_repo.next_story_key(db, project.id, project.key)

    # Insert
    story = await story_repo.create(
        db,
        project_id=project.id,
        story_key=key,
        title=body.title,
        description=body.description,
        epic_id=body.epic_id,
        status=StoryStatus(effective_status),
        priority=Priority(body.priority),
        story_points=body.story_points,
        assignee_id=body.assignee_id,
        reporter_id=user.id,
        due_date=body.due_date,
    )
    # Log activity: story created
    await log_activity(
        db,
        project_id=project.id,
        entity_type=ActivityEntityType.story,
        action=ActivityAction.created,
        actor_id=user.id,
        actor_name=user.name,
        story_id=story.id,
    )

    await db.commit()
    await db.refresh(story)

    logger.info(
        "Story created: key=%s project=%s by user=%s",
        story.story_key,
        project.id,
        user.id,
    )

    # Publish assigned event (if assignee is someone other than the actor)
    if body.assignee_id is not None and assignee_member is not None:
        payload = build_story_assigned_payload(
            project_id=project.id,
            project_name=project.name,
            story_id=story.id,
            story_key=story.story_key,
            story_title=story.title,
            assignee_id=body.assignee_id,
            assignee_email=assignee_member.email,
            assignee_name=assignee_member.name,
            actor_id=user.id,
            actor_name=user.name,
        )
        await publish_event(EVENT_STORY_ASSIGNED, payload)

    return await _to_story_out(db, story, project.id)


async def get_story(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    membership: ProjectMembership,
) -> StoryOut:
    """Return a single active story. Raises StoryNotFoundError if absent."""
    story = await story_repo.get_active(db, story_id, membership.project_id)
    if story is None:
        raise StoryNotFoundError()
    return await _to_story_out(db, story, membership.project_id)


async def list_stories(
    db: AsyncSession,
    *,
    membership: ProjectMembership,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    assignee_ids: list[uuid.UUID] | None = None,
    priorities: list[str] | None = None,
    statuses: list[str] | None = None,
    epic_ids: list[uuid.UUID | None] | None = None,
    search: str | None = None,
    sort_by: str = "priority",
    sort_order: str = "desc",
) -> tuple[list[StoryOut], Pagination]:
    """Return paginated, filtered, sorted stories for a project."""
    # Clamp pagination
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)

    # Validate search length
    if search is not None and len(search) > MAX_SEARCH_LENGTH:
        raise ValidationError(f"Search query must be at most {MAX_SEARCH_LENGTH} characters")

    # Validate sort field
    if sort_by not in ALLOWED_SORT_FIELDS:
        raise ValidationError(f"sortBy must be one of {', '.join(ALLOWED_SORT_FIELDS)}")

    # Validate sort order
    if sort_order not in ("asc", "desc"):
        raise ValidationError("sortOrder must be 'asc' or 'desc'")

    rows, total = await story_repo.list_filtered(
        db,
        membership.project_id,
        page=page,
        page_size=page_size,
        assignee_ids=assignee_ids,
        priorities=priorities,
        statuses=statuses,
        epic_ids=epic_ids,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    items = [await _to_story_out(db, row, membership.project_id) for row in rows]
    return items, paginate(page, page_size, total)


async def update_story(
    db: AsyncSession,
    *,
    story: UserStory,
    project: Project,
    user: CurrentUser,
    membership: ProjectMembership,
    body: StoryPatch,
) -> StoryOut:
    """
    Partial update of a story.

    Validates all fields before persisting. Status transition uses the OLD
    assignee for the auth check. Events fire AFTER commit.
    """
    patch_data = body.model_dump(exclude_unset=True)
    if not patch_data:
        raise BadRequestError(ERR_NO_FIELDS_TO_UPDATE)

    # ── Permission: only reporter, assignee, or owner can edit ────────────
    assert_can_edit(story, user, membership)

    # ── Validate assignee ─────────────────────────────────────────────────
    new_assignee_member: ProjectMember | None = None
    if "assignee_id" in patch_data:
        new_assignee = patch_data["assignee_id"]
        if new_assignee is not None and new_assignee != story.assignee_id:
            new_assignee_member = await _assert_assignee_is_member(db, project.id, new_assignee)

    # ── Validate epic ─────────────────────────────────────────────────────
    if "epic_id" in patch_data and patch_data["epic_id"] is not None:
        await _assert_epic_in_project(db, project.id, patch_data["epic_id"])

    # ── Status transition + auth rule ─────────────────────────────────────
    if "status" in patch_data and patch_data["status"] is not None:
        new_status = patch_data["status"]
        old_status = story.status.value if isinstance(story.status, StoryStatus) else story.status
        if new_status != old_status:
            assert_transition_allowed(old_status, new_status)
            # Auth: only the OLD assignee or the owner can change status
            if story.assignee_id is not None:
                if user.id != story.assignee_id and membership.role != "owner":
                    raise ForbiddenError(ERR_STATUS_CHANGE_FORBIDDEN)

    # ── Determine events before mutation ──────────────────────────────────
    assigned_event = None
    unassigned_event = None

    if "assignee_id" in patch_data:
        new_assignee = patch_data["assignee_id"]
        old_assignee = story.assignee_id

        if new_assignee != old_assignee:
            if new_assignee is None and old_assignee is not None:
                # Load old assignee member row BEFORE mutation for email/name
                old_member = await member_repo.get(db, project.id, old_assignee)
                unassigned_event = build_story_unassigned_payload(
                    project_id=project.id,
                    project_name=project.name,
                    story_id=story.id,
                    story_key=story.story_key,
                    story_title=story.title,
                    previous_assignee_id=old_assignee,
                    previous_assignee_email=old_member.email if old_member else "",
                    previous_assignee_name=old_member.name if old_member else "",
                    actor_id=user.id,
                    actor_name=user.name,
                )
            elif new_assignee is not None:
                # new_assignee_member already loaded by _assert_assignee_is_member above
                assigned_event = build_story_assigned_payload(
                    project_id=project.id,
                    project_name=project.name,
                    story_id=story.id,
                    story_key=story.story_key,
                    story_title=story.title,
                    assignee_id=new_assignee,
                    assignee_email=new_assignee_member.email if new_assignee_member else "",
                    assignee_name=new_assignee_member.name if new_assignee_member else "",
                    actor_id=user.id,
                    actor_name=user.name,
                )

    # ── Capture old values for activity logging ─────────────────────────
    old_values: dict[str, str | None] = {}
    for field in patch_data:
        if field == "status":
            raw = story.status
            old_values["status"] = raw.value if isinstance(raw, StoryStatus) else raw
        elif field == "priority":
            raw = story.priority
            old_values["priority"] = raw.value if isinstance(raw, Priority) else raw
        elif field == "assignee_id":
            old_values["assignee_id"] = str(story.assignee_id) if story.assignee_id else None
        elif field == "epic_id":
            old_values["epic_id"] = str(story.epic_id) if story.epic_id else None
        elif field == "due_date":
            old_values["due_date"] = story.due_date.isoformat() if story.due_date else None
        elif field == "story_points":
            old_values["story_points"] = str(story.story_points) if story.story_points else None
        else:
            old_values[field] = getattr(story, field, None)

    # ── Persist ───────────────────────────────────────────────────────────
    old_assignee_id = story.assignee_id  # snapshot before mutation
    for field, value in patch_data.items():
        if field == "status" and value is not None:
            setattr(story, field, StoryStatus(value))
        elif field == "priority" and value is not None:
            setattr(story, field, Priority(value))
        else:
            setattr(story, field, value)

    # ── Cascade assignee change to tasks/subtasks ─────────────────────────
    if "assignee_id" in patch_data and patch_data["assignee_id"] != old_assignee_id:
        await task_repo.update_assignee_for_story(db, story.id, patch_data["assignee_id"])

    # ── Log activity for each changed field ───────────────────────────────
    for field, value in patch_data.items():
        new_val: str | None
        if field == "status":
            new_val = value
        elif field == "priority":
            new_val = value
        elif field == "assignee_id":
            new_val = str(value) if value else None
        elif field == "epic_id":
            new_val = str(value) if value else None
        elif field == "due_date":
            new_val = value.isoformat() if value else None
        elif field == "story_points":
            new_val = str(value) if value else None
        else:
            new_val = value

        old_val = old_values.get(field)

        # Skip no-op changes
        if str(old_val) == str(new_val):
            continue

        # Determine action type
        if field == "status":
            action = ActivityAction.status_changed
        elif field == "assignee_id":
            action = ActivityAction.assigned
            # Resolve UUIDs → member names for human-readable logs
            if new_val is not None:
                new_val = new_assignee_member.name if new_assignee_member else new_val
            if old_val is not None:
                old_member_row = await member_repo.get(db, project.id, uuid.UUID(old_val))
                old_val = old_member_row.name if old_member_row else old_val
        else:
            action = ActivityAction.field_updated

        await log_activity(
            db,
            project_id=project.id,
            entity_type=ActivityEntityType.story,
            action=action,
            actor_id=user.id,
            actor_name=user.name,
            story_id=story.id,
            field_name=field,
            old_value=str(old_val) if old_val is not None else None,
            new_value=str(new_val) if new_val is not None else None,
        )

    await db.commit()
    await db.refresh(story)

    # ── Emit events after commit ──────────────────────────────────────────
    if assigned_event:
        await publish_event(EVENT_STORY_ASSIGNED, assigned_event)
    if unassigned_event:
        await publish_event(EVENT_STORY_UNASSIGNED, unassigned_event)

    return await _to_story_out(db, story, project.id)


async def delete_story(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    project: Project,
    user: CurrentUser,
    membership: ProjectMembership,
) -> None:
    """Soft-delete a story and cascade to tasks + comments."""
    story = await story_repo.get_active(db, story_id, project.id)
    if story is None:
        raise StoryNotFoundError()

    assert_can_delete(story, user, membership)

    # Log activity BEFORE soft-delete (story_id FK will remain valid)
    await log_activity(
        db,
        project_id=project.id,
        entity_type=ActivityEntityType.story,
        action=ActivityAction.deleted,
        actor_id=user.id,
        actor_name=user.name,
        story_id=story_id,
    )

    # Soft-delete the story
    await story_repo.soft_delete(db, story_id)

    # Cascade to tasks (table exists — model imported at module level)
    await db.execute(update(Task).where(Task.story_id == story_id).values(is_deleted=True))

    # Cascade to comments
    await db.execute(
        update(Comment).where(Comment.user_story_id == story_id).values(is_deleted=True)
    )

    await db.commit()

    logger.info("Story soft-deleted: id=%s project=%s by user=%s", story_id, project.id, user.id)
