"""Pydantic models for parsing inbound event payloads from RabbitMQ."""

from pydantic import BaseModel


class MemberAddedPayload(BaseModel):
    project_id: str
    project_name: str
    project_key: str
    added_user_id: str
    added_user_email: str
    added_user_name: str
    actor_id: str
    actor_name: str


class OwnershipTransferredPayload(BaseModel):
    project_id: str
    project_name: str
    new_owner_id: str
    new_owner_email: str
    new_owner_name: str
    previous_owner_id: str
    previous_owner_name: str
    actor_id: str


class StoryAssignedPayload(BaseModel):
    project_id: str
    project_name: str
    story_id: str
    story_key: str
    story_title: str
    assignee_id: str
    assignee_email: str
    assignee_name: str
    actor_id: str
    actor_name: str


class StoryUnassignedPayload(BaseModel):
    project_id: str
    project_name: str
    story_id: str
    story_key: str
    story_title: str
    previous_assignee_id: str
    previous_assignee_email: str
    previous_assignee_name: str
    actor_id: str
    actor_name: str


class CommentCreatedPayload(BaseModel):
    project_id: str
    project_name: str
    story_id: str
    story_key: str
    story_title: str
    comment_id: str
    comment_author_id: str
    comment_author_name: str
    comment_body_excerpt: str
    reporter_id: str
    reporter_email: str
    reporter_name: str
    assignee_id: str | None = None
    assignee_email: str | None = None
    assignee_name: str | None = None
