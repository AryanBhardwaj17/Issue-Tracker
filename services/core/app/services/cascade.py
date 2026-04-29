"""
Cascade soft-delete helpers.

Each function sets ``is_deleted=True`` on every row that belongs to a
project. Implemented as a single-pass multi-table update so it commits
in one transaction with the caller.
"""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.epic import Epic
from app.models.project import Project
from app.models.story import UserStory
from app.models.task import Task


async def cascade_soft_delete_project(db: AsyncSession, project_id: uuid.UUID) -> None:
    """
    Soft-delete a project and all its descendants in dependency order.

    Order matters — children before parents so FK constraints are never
    violated if hard-deletes are introduced later.
    """
    # 1. Tasks (includes subtasks via project_id)
    await db.execute(update(Task).where(Task.project_id == project_id).values(is_deleted=True))

    # 2. Comments — linked via user_story_id; cascade through stories
    story_ids_sq = select(UserStory.id).where(UserStory.project_id == project_id).scalar_subquery()
    await db.execute(
        update(Comment).where(Comment.user_story_id.in_(story_ids_sq)).values(is_deleted=True)
    )

    # 3. Stories
    await db.execute(
        update(UserStory).where(UserStory.project_id == project_id).values(is_deleted=True)
    )

    # 4. Epics
    await db.execute(update(Epic).where(Epic.project_id == project_id).values(is_deleted=True))

    # 5. Project itself
    await db.execute(update(Project).where(Project.id == project_id).values(is_deleted=True))
