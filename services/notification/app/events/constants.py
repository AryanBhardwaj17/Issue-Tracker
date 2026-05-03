"""Event type string constants — prevents typos across consumer and handlers."""

EVENT_MEMBER_ADDED = "member.added"
EVENT_OWNERSHIP_TRANSFERRED = "ownership.transferred"
EVENT_STORY_ASSIGNED = "story.assigned"
EVENT_STORY_UNASSIGNED = "story.unassigned"
EVENT_COMMENT_CREATED = "comment.created"

ALL_EVENT_TYPES = frozenset({
    EVENT_MEMBER_ADDED,
    EVENT_OWNERSHIP_TRANSFERRED,
    EVENT_STORY_ASSIGNED,
    EVENT_STORY_UNASSIGNED,
    EVENT_COMMENT_CREATED,
})
