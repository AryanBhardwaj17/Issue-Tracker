"""
Integration tests for the comment service.

Uses the in-memory SQLite DB from conftest.py, exercising the full
service → repository → DB path.
"""

import uuid

import pytest

from app.api.deps import ProjectMembership
from app.core.exceptions import CommentNotFoundError
from app.models.project import Project
from app.models.project_member import MemberRole, ProjectMember
from app.models.story import Priority, StoryStatus, UserStory
from app.schemas.comment import CommentCreate, CommentUpdate
from app.services import comment as comment_service

# ── Setup helpers ─────────────────────────────────────────────────────────────


async def _setup_project_with_member(db, user) -> Project:
    project = Project(name="Test", key="INT", owner_id=user.id, description=None)
    db.add(project)
    await db.flush()
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        name=user.name,
        role=MemberRole.OWNER,
    )
    db.add(member)
    await db.flush()
    return project


async def _setup_story(db, project: Project, reporter_id: uuid.UUID) -> UserStory:
    from sqlalchemy import text

    await db.execute(
        text("UPDATE projects SET next_story_seq = next_story_seq + 1 WHERE id = :pid"),
        {"pid": str(project.id)},
    )
    story = UserStory(
        project_id=project.id,
        story_key=f"{project.key}-1",
        title="Story",
        status=StoryStatus.BACKLOG,
        priority=Priority.MEDIUM,
        reporter_id=reporter_id,
    )
    db.add(story)
    await db.flush()
    return story


def _ms(project_id: uuid.UUID, user_id: uuid.UUID, role: str = "owner") -> ProjectMembership:
    return ProjectMembership(user_id=user_id, project_id=project_id, name="", role=role)


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_lifecycle(db, user_alice):
    """Create → list → edit → delete round-trip."""
    project = await _setup_project_with_member(db, user_alice)
    story = await _setup_story(db, project, user_alice.id)
    await db.commit()

    ms = _ms(project.id, user_alice.id)

    # Create
    created = await comment_service.create_comment(
        db,
        story_id=story.id,
        user=user_alice,
        membership=ms,
        body_data=CommentCreate(body="Hello"),
    )
    assert created.body == "Hello"
    assert created.image_url is None

    # List
    items, pagination = await comment_service.list_comments(
        db, story_id=story.id, membership=ms, page=1, page_size=25
    )
    assert len(items) == 1
    assert pagination.total == 1

    # Edit
    edited = await comment_service.edit_comment(
        db,
        story_id=story.id,
        comment_id=created.id,
        user=user_alice,
        membership=ms,
        body_data=CommentUpdate(body="Updated"),
    )
    assert edited.body == "Updated"

    # Delete
    await comment_service.delete_comment(
        db,
        story_id=story.id,
        comment_id=created.id,
        user=user_alice,
        membership=ms,
    )

    # After delete — list should return 0
    items, pagination = await comment_service.list_comments(
        db, story_id=story.id, membership=ms, page=1, page_size=25
    )
    assert len(items) == 0
    assert pagination.total == 0


@pytest.mark.asyncio
async def test_pagination_oldest_first(db, user_alice):
    """5 comments, page size 2: first page has the 2 oldest."""
    project = await _setup_project_with_member(db, user_alice)
    story = await _setup_story(db, project, user_alice.id)
    await db.commit()

    ms = _ms(project.id, user_alice.id)

    bodies = ["one", "two", "three", "four", "five"]
    for body in bodies:
        await comment_service.create_comment(
            db,
            story_id=story.id,
            user=user_alice,
            membership=ms,
            body_data=CommentCreate(body=body),
        )

    # Page 1
    page1, pagination = await comment_service.list_comments(
        db, story_id=story.id, membership=ms, page=1, page_size=2
    )
    assert len(page1) == 2
    assert page1[0].body == "one"
    assert page1[1].body == "two"
    assert pagination.total == 5
    assert pagination.total_pages == 3

    # Page 3
    page3, _ = await comment_service.list_comments(
        db, story_id=story.id, membership=ms, page=3, page_size=2
    )
    assert len(page3) == 1
    assert page3[0].body == "five"


@pytest.mark.asyncio
async def test_updated_at_advances_after_edit(db, user_alice):
    """updatedAt must be strictly greater than createdAt after an edit."""
    import asyncio

    project = await _setup_project_with_member(db, user_alice)
    story = await _setup_story(db, project, user_alice.id)
    await db.commit()

    ms = _ms(project.id, user_alice.id)

    created = await comment_service.create_comment(
        db,
        story_id=story.id,
        user=user_alice,
        membership=ms,
        body_data=CommentCreate(body="original"),
    )
    created_at = created.created_at

    # Small sleep so updated_at timestamp advances (SQLite uses Python datetime)
    await asyncio.sleep(0.01)

    edited = await comment_service.edit_comment(
        db,
        story_id=story.id,
        comment_id=created.id,
        user=user_alice,
        membership=ms,
        body_data=CommentUpdate(body="edited"),
    )

    assert edited.updated_at > created_at


@pytest.mark.asyncio
async def test_comment_belongs_to_wrong_story_returns_404(db, user_alice):
    """A comment belonging to story A should 404 when accessed via story B's URL."""
    project = await _setup_project_with_member(db, user_alice)
    story_a = await _setup_story(db, project, user_alice.id)

    # Create story B manually
    story_b = UserStory(
        project_id=project.id,
        story_key=f"{project.key}-2",
        title="Story B",
        status=StoryStatus.BACKLOG,
        priority=Priority.MEDIUM,
        reporter_id=user_alice.id,
    )
    db.add(story_b)
    await db.flush()
    await db.commit()

    ms = _ms(project.id, user_alice.id)

    # Create a comment on story A
    comment = await comment_service.create_comment(
        db,
        story_id=story_a.id,
        user=user_alice,
        membership=ms,
        body_data=CommentCreate(body="on story A"),
    )

    # Try to delete it via story B's path
    with pytest.raises(CommentNotFoundError):
        await comment_service.delete_comment(
            db,
            story_id=story_b.id,  # wrong story
            comment_id=comment.id,
            user=user_alice,
            membership=ms,
        )


@pytest.mark.asyncio
async def test_cross_story_comment_isolation(db, user_alice):
    """Comments from story A must not appear in story B's list."""
    project = await _setup_project_with_member(db, user_alice)
    story_a = await _setup_story(db, project, user_alice.id)

    story_b = UserStory(
        project_id=project.id,
        story_key=f"{project.key}-2",
        title="Story B",
        status=StoryStatus.BACKLOG,
        priority=Priority.MEDIUM,
        reporter_id=user_alice.id,
    )
    db.add(story_b)
    await db.flush()
    await db.commit()

    ms = _ms(project.id, user_alice.id)

    # 2 comments on story A
    for body in ["A1", "A2"]:
        await comment_service.create_comment(
            db,
            story_id=story_a.id,
            user=user_alice,
            membership=ms,
            body_data=CommentCreate(body=body),
        )

    # Story B has no comments
    items, pagination = await comment_service.list_comments(
        db, story_id=story_b.id, membership=ms, page=1, page_size=25
    )
    assert len(items) == 0
    assert pagination.total == 0
