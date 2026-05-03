"""
Unit tests for the comment service.

Uses the in-memory SQLite DB from conftest.py.
File I/O is mocked via unittest.mock.patch to keep tests fast and
deterministic — the upload service has its own file I/O tests.
"""

import uuid
from unittest.mock import patch

import pytest

from app.api.deps import ProjectMembership
from app.core.exceptions import CommentNotFoundError, ForbiddenError, StoryNotFoundError
from app.models.comment import Comment
from app.models.project import Project
from app.models.project_member import MemberRole, ProjectMember
from app.models.story import Priority, StoryStatus, UserStory
from app.services import comment as comment_service

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _create_project(db, owner_id: uuid.UUID) -> Project:
    project = Project(
        name="Test Project",
        key="TEST",
        owner_id=owner_id,
        description=None,
    )
    db.add(project)
    await db.flush()
    return project


async def _add_member(
    db, project_id: uuid.UUID, user_id: uuid.UUID, name: str, role: MemberRole
) -> ProjectMember:
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        name=name,
        role=role,
    )
    db.add(member)
    await db.flush()
    return member


async def _create_story(db, project: Project, reporter_id: uuid.UUID) -> UserStory:
    from sqlalchemy import text

    await db.execute(
        text("UPDATE projects SET next_story_seq = next_story_seq + 1 WHERE id = :pid"),
        {"pid": str(project.id)},
    )
    story = UserStory(
        project_id=project.id,
        story_key=f"{project.key}-1",
        title="Test Story",
        status=StoryStatus.BACKLOG,
        priority=Priority.MEDIUM,
        reporter_id=reporter_id,
    )
    db.add(story)
    await db.flush()
    return story


async def _create_comment(
    db,
    story_id: uuid.UUID,
    author_id: uuid.UUID,
    body: str = "A test comment",
    image_url: str | None = None,
) -> Comment:
    comment = Comment(
        user_story_id=story_id,
        author_id=author_id,
        body=body,
        image_url=image_url,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    return comment


def _membership(
    project_id: uuid.UUID, user_id: uuid.UUID, role: str = "member"
) -> ProjectMembership:
    return ProjectMembership(user_id=user_id, project_id=project_id, name="Test", role=role)


# ── Tests: create_comment ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_comment_happy_path(db, user_alice):
    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    story = await _create_story(db, project, user_alice.id)
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")
    from app.schemas.comment import CommentCreate

    result = await comment_service.create_comment(
        db,
        story_id=story.id,
        user=user_alice,
        membership=membership,
        body_data=CommentCreate(body="Hello world"),
    )

    assert result.body == "Hello world"
    assert result.author.id == user_alice.id
    assert result.author.name == user_alice.name
    assert result.image_url is None


@pytest.mark.asyncio
async def test_create_comment_story_not_found(db, user_alice):
    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")
    from app.schemas.comment import CommentCreate

    with pytest.raises(StoryNotFoundError):
        await comment_service.create_comment(
            db,
            story_id=uuid.uuid4(),
            user=user_alice,
            membership=membership,
            body_data=CommentCreate(body="test"),
        )


@pytest.mark.asyncio
async def test_create_comment_deleted_story(db, user_alice):
    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    story = await _create_story(db, project, user_alice.id)
    story.is_deleted = True
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")
    from app.schemas.comment import CommentCreate

    with pytest.raises(StoryNotFoundError):
        await comment_service.create_comment(
            db,
            story_id=story.id,
            user=user_alice,
            membership=membership,
            body_data=CommentCreate(body="test"),
        )


# ── Tests: list_comments ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_comments_oldest_first(db, user_alice):

    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    story = await _create_story(db, project, user_alice.id)

    await _create_comment(db, story.id, user_alice.id, "First")
    await _create_comment(db, story.id, user_alice.id, "Second")
    await _create_comment(db, story.id, user_alice.id, "Third")
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")
    items, pagination = await comment_service.list_comments(
        db, story_id=story.id, membership=membership, page=1, page_size=25
    )

    assert len(items) == 3
    assert items[0].body == "First"
    assert items[1].body == "Second"
    assert items[2].body == "Third"
    assert pagination.total == 3


# ── Tests: edit_comment ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_edit_comment_by_author(db, user_alice):
    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    story = await _create_story(db, project, user_alice.id)
    comment = await _create_comment(db, story.id, user_alice.id, "Original")
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")
    from app.schemas.comment import CommentUpdate

    result = await comment_service.edit_comment(
        db,
        story_id=story.id,
        comment_id=comment.id,
        user=user_alice,
        membership=membership,
        body_data=CommentUpdate(body="Updated"),
    )

    assert result.body == "Updated"
    assert result.updated_at >= result.created_at


@pytest.mark.asyncio
async def test_edit_comment_by_non_author_raises_403(db, user_alice, user_bob):
    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    await _add_member(db, project.id, user_bob.id, user_bob.name, MemberRole.MEMBER)
    story = await _create_story(db, project, user_alice.id)
    # Alice creates the comment
    comment = await _create_comment(db, story.id, user_alice.id, "Alice's comment")
    await db.commit()

    # Bob (a plain member) tries to edit — should be 403
    membership_bob = _membership(project.id, user_bob.id, "member")
    from app.schemas.comment import CommentUpdate

    with pytest.raises(ForbiddenError):
        await comment_service.edit_comment(
            db,
            story_id=story.id,
            comment_id=comment.id,
            user=user_bob,
            membership=membership_bob,
            body_data=CommentUpdate(body="Hacked"),
        )


@pytest.mark.asyncio
async def test_edit_comment_by_owner_raises_403(db, user_alice, user_bob):
    """Even the project owner cannot edit another member's comment."""
    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    await _add_member(db, project.id, user_bob.id, user_bob.name, MemberRole.MEMBER)
    story = await _create_story(db, project, user_alice.id)
    # Bob creates the comment
    comment = await _create_comment(db, story.id, user_bob.id, "Bob's comment")
    await db.commit()

    # Alice is the owner but not the author
    membership_alice = _membership(project.id, user_alice.id, "owner")
    from app.schemas.comment import CommentUpdate

    with pytest.raises(ForbiddenError):
        await comment_service.edit_comment(
            db,
            story_id=story.id,
            comment_id=comment.id,
            user=user_alice,
            membership=membership_alice,
            body_data=CommentUpdate(body="Owner override"),
        )


@pytest.mark.asyncio
async def test_edit_comment_replace_image_unlinks_old(db, user_alice, monkeypatch, tmp_path):

    monkeypatch.setattr("app.services.comment.settings.UPLOADS_DIR", str(tmp_path))

    # Create an actual old file on disk
    old_filename = "old-image.png"
    old_path = tmp_path / old_filename
    old_path.write_bytes(b"olddata")
    old_url = f"/uploads/{old_filename}"

    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    story = await _create_story(db, project, user_alice.id)
    comment = await _create_comment(db, story.id, user_alice.id, "body", image_url=old_url)
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")
    from app.schemas.comment import CommentUpdate

    result = await comment_service.edit_comment(
        db,
        story_id=story.id,
        comment_id=comment.id,
        user=user_alice,
        membership=membership,
        body_data=CommentUpdate(image_url="/uploads/new-image.png"),
    )

    assert result.image_url == "/uploads/new-image.png"
    # Old file must be gone
    assert not old_path.exists()


@pytest.mark.asyncio
async def test_edit_comment_remove_image(db, user_alice, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.comment.settings.UPLOADS_DIR", str(tmp_path))

    old_filename = "to-remove.png"
    (tmp_path / old_filename).write_bytes(b"data")
    old_url = f"/uploads/{old_filename}"

    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    story = await _create_story(db, project, user_alice.id)
    comment = await _create_comment(db, story.id, user_alice.id, "body", image_url=old_url)
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")
    from app.schemas.comment import CommentUpdate

    result = await comment_service.edit_comment(
        db,
        story_id=story.id,
        comment_id=comment.id,
        user=user_alice,
        membership=membership,
        body_data=CommentUpdate(remove_image=True),
    )

    assert result.image_url is None
    assert not (tmp_path / old_filename).exists()


@pytest.mark.asyncio
async def test_edit_no_image_does_not_call_unlink(db, user_alice):
    """Body-only edit with no old image must not attempt any file deletion."""
    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    story = await _create_story(db, project, user_alice.id)
    comment = await _create_comment(db, story.id, user_alice.id, "original", image_url=None)
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")
    from app.schemas.comment import CommentUpdate

    with patch("app.services.comment.os.unlink") as mock_unlink:
        await comment_service.edit_comment(
            db,
            story_id=story.id,
            comment_id=comment.id,
            user=user_alice,
            membership=membership,
            body_data=CommentUpdate(body="updated body"),
        )
        mock_unlink.assert_not_called()


# ── Tests: delete_comment ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_comment_by_author(db, user_alice, monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.comment.settings.UPLOADS_DIR", str(tmp_path))

    img_filename = "delete-me.png"
    (tmp_path / img_filename).write_bytes(b"img")
    img_url = f"/uploads/{img_filename}"

    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    story = await _create_story(db, project, user_alice.id)
    comment = await _create_comment(db, story.id, user_alice.id, "bye", image_url=img_url)
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")

    await comment_service.delete_comment(
        db,
        story_id=story.id,
        comment_id=comment.id,
        user=user_alice,
        membership=membership,
    )

    # Image file must be deleted
    assert not (tmp_path / img_filename).exists()

    # Comment must be soft-deleted in DB
    from sqlalchemy import select

    from app.models.comment import Comment as CommentModel

    row = (await db.execute(select(CommentModel).where(CommentModel.id == comment.id))).scalar_one()
    assert row.is_deleted is True


@pytest.mark.asyncio
async def test_delete_comment_by_owner(db, user_alice, user_bob):
    """Project owner can delete any comment even if they are not the author."""
    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    await _add_member(db, project.id, user_bob.id, user_bob.name, MemberRole.MEMBER)
    story = await _create_story(db, project, user_alice.id)
    comment = await _create_comment(db, story.id, user_bob.id, "Bob's comment")
    await db.commit()

    # Alice is owner, not author
    membership_alice = _membership(project.id, user_alice.id, "owner")

    # Should NOT raise
    await comment_service.delete_comment(
        db,
        story_id=story.id,
        comment_id=comment.id,
        user=user_alice,
        membership=membership_alice,
    )


@pytest.mark.asyncio
async def test_delete_comment_by_plain_member_raises_403(db, user_alice, user_bob):
    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    await _add_member(db, project.id, user_bob.id, user_bob.name, MemberRole.MEMBER)
    story = await _create_story(db, project, user_alice.id)
    # Alice creates the comment, Bob tries to delete
    comment = await _create_comment(db, story.id, user_alice.id, "Alice's comment")
    await db.commit()

    membership_bob = _membership(project.id, user_bob.id, "member")

    with pytest.raises(ForbiddenError):
        await comment_service.delete_comment(
            db,
            story_id=story.id,
            comment_id=comment.id,
            user=user_bob,
            membership=membership_bob,
        )


@pytest.mark.asyncio
async def test_delete_file_not_found_swallowed(db, user_alice, monkeypatch, tmp_path):
    """FileNotFoundError during unlink must not propagate."""
    monkeypatch.setattr("app.services.comment.settings.UPLOADS_DIR", str(tmp_path))

    # Image URL points to a file that does NOT exist
    img_url = "/uploads/already-gone.png"

    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    story = await _create_story(db, project, user_alice.id)
    comment = await _create_comment(db, story.id, user_alice.id, "bye", image_url=img_url)
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")

    # Should not raise even though the file is missing
    await comment_service.delete_comment(
        db,
        story_id=story.id,
        comment_id=comment.id,
        user=user_alice,
        membership=membership,
    )


@pytest.mark.asyncio
async def test_delete_already_deleted_comment_raises_404(db, user_alice):
    project = await _create_project(db, user_alice.id)
    await _add_member(db, project.id, user_alice.id, user_alice.name, MemberRole.OWNER)
    story = await _create_story(db, project, user_alice.id)
    comment = await _create_comment(db, story.id, user_alice.id, "gone")
    comment.is_deleted = True
    await db.commit()

    membership = _membership(project.id, user_alice.id, "owner")

    with pytest.raises(CommentNotFoundError):
        await comment_service.delete_comment(
            db,
            story_id=story.id,
            comment_id=comment.id,
            user=user_alice,
            membership=membership,
        )
