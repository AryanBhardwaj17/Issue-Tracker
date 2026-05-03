"""
Comment service — business logic for the Comment aggregate.

Responsibilities:
- Create, list, edit, soft-delete comments.
- Author-only edit guard (ForbiddenError for anyone else, including the project owner).
- Author-or-owner delete guard.
- Best-effort image file cleanup on edit (replace / remove) and delete.
  Cleanup runs AFTER the DB commit so a failed unlink never rolls back data changes.
- Domain event stub: comment.created (wired for real in E5-S2).
"""

import logging
import os
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, ProjectMembership
from app.core.config import settings
from app.core.exceptions import CommentNotFoundError, ForbiddenError, StoryNotFoundError
from app.events.constants import EVENT_COMMENT_CREATED
from app.events.payloads import build_comment_created_payload
from app.events.publisher import publish_event
from app.repositories import comment as comment_repo
from app.repositories import project as project_repo
from app.repositories import project_members as member_repo
from app.repositories import story as story_repo
from app.schemas.comment import AuthorRef, CommentCreate, CommentOut, CommentUpdate
from app.schemas.common import Pagination, paginate
from app.utils.constants import ERR_COMMENT_DELETE_FORBIDDEN, ERR_COMMENT_EDIT_FORBIDDEN

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _unlink_image(image_url: str) -> None:
    """
    Delete an image file from disk by its relative URL.

    ``image_url`` must be in the form ``/uploads/<filename>``.
    FileNotFoundError is swallowed silently — file already gone is not an error.
    Any other OSError is logged as a warning but never re-raised so callers
    are never disrupted by a filesystem issue.
    """
    if not image_url.startswith("/uploads/"):
        logger.warning("Skipping unlink for unexpected image_url format: %s", image_url)
        return
    filename = image_url[len("/uploads/") :]
    path = os.path.join(settings.UPLOADS_DIR, filename)
    try:
        os.unlink(path)
        logger.info("Deleted image file: %s", path)
    except FileNotFoundError:
        pass  # Already gone — not an error
    except OSError as exc:
        logger.warning("Could not delete image file %s: %s", path, exc)


async def _resolve_author(
    db: AsyncSession, project_id: uuid.UUID, author_id: uuid.UUID
) -> AuthorRef:
    """Look up the author's display name from project_members. Falls back to empty string."""
    member = await member_repo.get(db, project_id, author_id)
    name = member.name if member else ""
    return AuthorRef(id=author_id, name=name)


async def _to_comment_out(db: AsyncSession, comment, project_id: uuid.UUID) -> CommentOut:
    """Convert a Comment ORM row to the response DTO with resolved author name."""
    author = await _resolve_author(db, project_id, comment.author_id)
    return CommentOut(
        id=comment.id,
        user_story_id=comment.user_story_id,
        author=author,
        body=comment.body,
        image_url=comment.image_url,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


# ── Service functions ─────────────────────────────────────────────────────────


async def create_comment(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    user: CurrentUser,
    membership: ProjectMembership,
    body_data: CommentCreate,
) -> CommentOut:
    """
    Create a comment on a story. Caller must be a project member.

    Publishes ``comment.created`` event stub after commit.
    """
    # Validate story exists and is not soft-deleted
    story = await story_repo.get_active(db, story_id, membership.project_id)
    if story is None:
        raise StoryNotFoundError()

    comment = await comment_repo.create(
        db,
        user_story_id=story_id,
        author_id=user.id,
        body=body_data.body,
        image_url=body_data.image_url,
    )
    await db.commit()
    await db.refresh(comment)

    # Publish event — load project + recipient member rows for self-contained payload
    project = await project_repo.get_by_id(db, membership.project_id)
    reporter_member = await member_repo.get(db, membership.project_id, story.reporter_id)
    assignee_member = None
    if story.assignee_id is not None:
        assignee_member = await member_repo.get(db, membership.project_id, story.assignee_id)

    payload = build_comment_created_payload(
        project_id=membership.project_id,
        project_name=project.name if project else "",
        story_id=story_id,
        story_key=story.story_key,
        story_title=story.title,
        comment_id=comment.id,
        comment_author_id=user.id,
        comment_author_name=user.name,
        reporter_id=story.reporter_id,
        reporter_email=reporter_member.email if reporter_member else "",
        reporter_name=reporter_member.name if reporter_member else "",
        assignee_id=story.assignee_id,
        assignee_email=assignee_member.email if assignee_member else None,
        assignee_name=assignee_member.name if assignee_member else None,
        body_excerpt=comment.body,
    )
    await publish_event(EVENT_COMMENT_CREATED, payload)

    return await _to_comment_out(db, comment, membership.project_id)


async def list_comments(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    membership: ProjectMembership,
    page: int,
    page_size: int,
) -> tuple[list[CommentOut], Pagination]:
    """List active comments for a story, oldest first."""
    story = await story_repo.get_active(db, story_id, membership.project_id)
    if story is None:
        raise StoryNotFoundError()

    rows, total = await comment_repo.list_for_story(
        db, story_id=story_id, page=page, page_size=page_size
    )
    items = [await _to_comment_out(db, c, membership.project_id) for c in rows]
    pagination = paginate(page, page_size, total)
    return items, pagination


async def edit_comment(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    comment_id: uuid.UUID,
    user: CurrentUser,
    membership: ProjectMembership,
    body_data: CommentUpdate,
) -> CommentOut:
    """
    Edit a comment. Only the original author may edit — owner cannot.

    On image replacement or removal, the old file is deleted best-effort
    AFTER the DB commit so a failed unlink never rolls back the edit.
    """
    # Validate story
    story = await story_repo.get_active(db, story_id, membership.project_id)
    if story is None:
        raise StoryNotFoundError()

    # Fetch and validate comment
    comment = await comment_repo.get_by_id(db, comment_id)
    if comment is None or comment.is_deleted:
        raise CommentNotFoundError()

    # Verify the comment belongs to this story (prevents cross-story access)
    if comment.user_story_id != story_id:
        raise CommentNotFoundError()

    # Author-only guard — even the project owner cannot edit another member's comment
    if comment.author_id != user.id:
        raise ForbiddenError(ERR_COMMENT_EDIT_FORBIDDEN)

    # Capture old image URL before any mutation
    old_image_url = comment.image_url

    # Apply body update
    if body_data.body is not None:
        comment.body = body_data.body

    # Apply image update: remove_image takes precedence over image_url
    if body_data.remove_image:
        comment.image_url = None
    elif body_data.image_url is not None:
        comment.image_url = body_data.image_url

    await db.commit()
    await db.refresh(comment)

    # Best-effort cleanup of old image file AFTER successful commit
    should_delete_old = (
        old_image_url is not None
        and (body_data.remove_image or body_data.image_url is not None)
        and old_image_url != comment.image_url
    )
    if should_delete_old:
        _unlink_image(old_image_url)

    return await _to_comment_out(db, comment, membership.project_id)


async def delete_comment(
    db: AsyncSession,
    *,
    story_id: uuid.UUID,
    comment_id: uuid.UUID,
    user: CurrentUser,
    membership: ProjectMembership,
) -> None:
    """
    Soft-delete a comment. Author or project owner may delete.

    The image binary is deleted from disk AFTER the DB commit.
    FileNotFoundError is silently swallowed.
    """
    # Validate story
    story = await story_repo.get_active(db, story_id, membership.project_id)
    if story is None:
        raise StoryNotFoundError()

    # Fetch and validate comment
    comment = await comment_repo.get_by_id(db, comment_id)
    if comment is None or comment.is_deleted:
        raise CommentNotFoundError()

    # Verify it belongs to this story
    if comment.user_story_id != story_id:
        raise CommentNotFoundError()

    # Author or project owner can delete
    if comment.author_id != user.id and membership.role != "owner":
        raise ForbiddenError(ERR_COMMENT_DELETE_FORBIDDEN)

    # Capture image URL before soft-delete
    image_url = comment.image_url

    await comment_repo.soft_delete(db, comment_id)
    await db.commit()

    # Delete image binary after successful commit
    if image_url:
        _unlink_image(image_url)
