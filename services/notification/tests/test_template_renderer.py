"""Unit tests for the Jinja2 template renderer — rendering, XSS escaping, excerpt ellipsis."""

import pytest

from app.events.payloads import (
    CommentCreatedPayload,
    MemberAddedPayload,
    OwnershipTransferredPayload,
    StoryAssignedPayload,
    StoryUnassignedPayload,
)
from app.services.template_renderer import render_template

from tests.factories import (
    make_comment_created_payload,
    make_member_added_payload,
    make_ownership_transferred_payload,
    make_story_assigned_payload,
    make_story_unassigned_payload,
)


FRONTEND_URL = "http://localhost:3000"


# ── Each template renders without error ──────────────────────────────────────


class TestTemplatesRender:
    def test_member_added_renders(self):
        payload = MemberAddedPayload.model_validate(make_member_added_payload())
        html = render_template(
            "member_added.html",
            payload=payload,
            recipient_name=payload.added_user_name,
            link=f"{FRONTEND_URL}/projects/{payload.project_id}/board",
        )
        assert "Added to Project" in html
        assert payload.actor_name in html
        assert payload.project_name in html
        assert payload.added_user_name in html
        assert "Open Project" in html

    def test_ownership_transferred_renders(self):
        payload = OwnershipTransferredPayload.model_validate(
            make_ownership_transferred_payload()
        )
        html = render_template(
            "ownership_transferred.html",
            payload=payload,
            recipient_name=payload.new_owner_name,
            link=f"{FRONTEND_URL}/projects/{payload.project_id}/settings",
        )
        assert "Ownership Transferred" in html
        assert payload.previous_owner_name in html
        assert payload.project_name in html
        assert "View Project Settings" in html

    def test_story_assigned_renders(self):
        payload = StoryAssignedPayload.model_validate(make_story_assigned_payload())
        html = render_template(
            "story_assigned.html",
            payload=payload,
            recipient_name=payload.assignee_name,
            link=f"{FRONTEND_URL}/projects/{payload.project_id}/stories/{payload.story_id}",
        )
        assert "Story Assigned" in html
        assert payload.actor_name in html
        assert payload.story_key in html
        assert payload.story_title in html
        assert "View Story" in html

    def test_story_unassigned_renders(self):
        payload = StoryUnassignedPayload.model_validate(make_story_unassigned_payload())
        html = render_template(
            "story_unassigned.html",
            payload=payload,
            recipient_name=payload.previous_assignee_name,
            link=f"{FRONTEND_URL}/projects/{payload.project_id}/stories/{payload.story_id}",
        )
        assert "Story Unassigned" in html
        assert payload.actor_name in html
        assert payload.story_key in html
        assert "View Story" in html

    def test_comment_created_renders(self):
        payload = CommentCreatedPayload.model_validate(make_comment_created_payload())
        html = render_template(
            "comment_created.html",
            payload=payload,
            recipient_name=payload.reporter_name,
            link=f"{FRONTEND_URL}/projects/{payload.project_id}/stories/{payload.story_id}",
        )
        assert "New Comment" in html
        assert payload.comment_author_name in html
        assert payload.story_key in html
        assert payload.comment_body_excerpt in html
        assert "View Comment" in html


# ── XSS escaping ─────────────────────────────────────────────────────────────


class TestXSSEscaping:
    def test_xss_in_project_name_escaped(self):
        """<script> tags in project_name must be rendered as text entities."""
        data = make_member_added_payload(project_name='<script>alert("xss")</script>')
        payload = MemberAddedPayload.model_validate(data)
        html = render_template(
            "member_added.html",
            payload=payload,
            recipient_name=payload.added_user_name,
            link=f"{FRONTEND_URL}/projects/{payload.project_id}/board",
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_xss_in_story_title_escaped(self):
        data = make_story_assigned_payload(story_title='<img src=x onerror=alert(1)>')
        payload = StoryAssignedPayload.model_validate(data)
        html = render_template(
            "story_assigned.html",
            payload=payload,
            recipient_name=payload.assignee_name,
            link=f"{FRONTEND_URL}/test",
        )
        assert "<img " not in html
        assert "&lt;img " in html

    def test_xss_in_actor_name_escaped(self):
        data = make_member_added_payload(actor_name='<b onmouseover="evil()">Hacker</b>')
        payload = MemberAddedPayload.model_validate(data)
        html = render_template(
            "member_added.html",
            payload=payload,
            recipient_name=payload.added_user_name,
            link=f"{FRONTEND_URL}/test",
        )
        assert 'onmouseover="evil()"' not in html
        assert "&lt;b " in html

    def test_xss_in_recipient_name_escaped(self):
        data = make_member_added_payload(added_user_name='<script>steal()</script>')
        payload = MemberAddedPayload.model_validate(data)
        html = render_template(
            "member_added.html",
            payload=payload,
            recipient_name=payload.added_user_name,
            link=f"{FRONTEND_URL}/test",
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_xss_in_comment_body_escaped(self):
        data = make_comment_created_payload(
            comment_body_excerpt='<script>document.cookie</script>'
        )
        payload = CommentCreatedPayload.model_validate(data)
        html = render_template(
            "comment_created.html",
            payload=payload,
            recipient_name="Bob",
            link=f"{FRONTEND_URL}/test",
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_xss_in_previous_owner_name_escaped(self):
        data = make_ownership_transferred_payload(
            previous_owner_name='<div onclick="hack()">'
        )
        payload = OwnershipTransferredPayload.model_validate(data)
        html = render_template(
            "ownership_transferred.html",
            payload=payload,
            recipient_name=payload.new_owner_name,
            link=f"{FRONTEND_URL}/test",
        )
        assert 'onclick="hack()"' not in html


# ── Comment excerpt ellipsis ─────────────────────────────────────────────────


class TestCommentExcerptEllipsis:
    def test_short_excerpt_no_ellipsis(self):
        """Excerpts shorter than 200 chars should NOT have ellipsis."""
        short_text = "This is a short comment."
        data = make_comment_created_payload(comment_body_excerpt=short_text)
        payload = CommentCreatedPayload.model_validate(data)
        html = render_template(
            "comment_created.html",
            payload=payload,
            recipient_name="Bob",
            link=f"{FRONTEND_URL}/test",
        )
        assert short_text in html
        # &#8230; is the HTML entity for … (ellipsis)
        assert "&#8230;" not in html

    def test_exactly_199_chars_no_ellipsis(self):
        text = "A" * 199
        data = make_comment_created_payload(comment_body_excerpt=text)
        payload = CommentCreatedPayload.model_validate(data)
        html = render_template(
            "comment_created.html",
            payload=payload,
            recipient_name="Bob",
            link=f"{FRONTEND_URL}/test",
        )
        assert "&#8230;" not in html

    def test_exactly_200_chars_has_ellipsis(self):
        """Excerpt of exactly 200 chars → ellipsis appended."""
        text = "B" * 200
        data = make_comment_created_payload(comment_body_excerpt=text)
        payload = CommentCreatedPayload.model_validate(data)
        html = render_template(
            "comment_created.html",
            payload=payload,
            recipient_name="Bob",
            link=f"{FRONTEND_URL}/test",
        )
        assert "&#8230;" in html

    def test_long_excerpt_has_ellipsis(self):
        """Excerpt over 200 chars → ellipsis appended."""
        text = "C" * 500
        data = make_comment_created_payload(comment_body_excerpt=text)
        payload = CommentCreatedPayload.model_validate(data)
        html = render_template(
            "comment_created.html",
            payload=payload,
            recipient_name="Bob",
            link=f"{FRONTEND_URL}/test",
        )
        assert "&#8230;" in html

    def test_empty_excerpt_no_ellipsis(self):
        data = make_comment_created_payload(comment_body_excerpt="")
        payload = CommentCreatedPayload.model_validate(data)
        html = render_template(
            "comment_created.html",
            payload=payload,
            recipient_name="Bob",
            link=f"{FRONTEND_URL}/test",
        )
        assert "&#8230;" not in html


# ── Base template structure ──────────────────────────────────────────────────


class TestBaseTemplate:
    def test_contains_header_and_footer(self):
        payload = MemberAddedPayload.model_validate(make_member_added_payload())
        html = render_template(
            "member_added.html",
            payload=payload,
            recipient_name="Bob",
            link=f"{FRONTEND_URL}/test",
        )
        assert "Issue Tracker" in html
        assert "automated notification" in html

    def test_link_is_full_url(self):
        payload = MemberAddedPayload.model_validate(make_member_added_payload())
        link = f"{FRONTEND_URL}/projects/{payload.project_id}/board"
        html = render_template(
            "member_added.html",
            payload=payload,
            recipient_name="Bob",
            link=link,
        )
        assert link in html

    def test_unicode_in_project_name(self):
        """Unicode/emoji characters render correctly."""
        data = make_member_added_payload(project_name="Проект 🚀 日本語")
        payload = MemberAddedPayload.model_validate(data)
        html = render_template(
            "member_added.html",
            payload=payload,
            recipient_name="Bob",
            link=f"{FRONTEND_URL}/test",
        )
        assert "Проект" in html
        assert "🚀" in html
        assert "日本語" in html
