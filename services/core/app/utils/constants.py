"""
Single source of truth for all magic values used across the Core Service.

Every schema constraint, validation rule, and user-facing error message must
be imported from here — never hard-coded inline. This makes changes atomic
and keeps the codebase easy to search.
"""

# ── Pagination ────────────────────────────────────────────────────────────────
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# ── Project field validation ──────────────────────────────────────────────────
PROJECT_NAME_MIN_LENGTH = 1
PROJECT_NAME_MAX_LENGTH = 200
PROJECT_DESCRIPTION_MAX_LENGTH = 10_000
PROJECT_KEY_MAX_LENGTH = 20

# ── Project key generation ────────────────────────────────────────────────────
MAX_KEY_RETRIES = 50  # attempts before KeyGenerationError is raised
KEY_BASE_MAX_LETTERS = 4  # take first N alpha chars for the key base

# ── Story validation ──────────────────────────────────────────────────────────
STORY_TITLE_MIN_LENGTH = 1
STORY_TITLE_MAX_LENGTH = 500
STORY_DESCRIPTION_MAX_LENGTH = 10_000
FIBONACCI_POINTS = frozenset({1, 2, 3, 5, 8, 13, 21})
MAX_SEARCH_LENGTH = 200
ALLOWED_SORT_FIELDS = ("priority", "created_at", "updated_at", "due_date", "story_key")

# ── Task / subtask ────────────────────────────────────────────────────────────
TASK_TITLE_MAX_LENGTH = 500
MAX_TASK_DEPTH = 2  # tasks (depth 1) + subtasks (depth 2) only

# ── Comment ───────────────────────────────────────────────────────────────────
COMMENT_BODY_MIN_LENGTH = 1
COMMENT_BODY_MAX_LENGTH = 10_000
ERR_COMMENT_NOT_FOUND = "Comment not found"
ERR_COMMENT_DELETE_FORBIDDEN = "Only the comment author or project owner can delete a comment"

# ── File upload ───────────────────────────────────────────────────────────────
ALLOWED_IMAGE_MIMES = frozenset({"image/png", "image/jpeg", "image/gif", "image/webp"})
MIME_TO_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
}

# ── User-facing error messages ────────────────────────────────────────────────
ERR_INVALID_TOKEN = "Invalid or expired access token"
ERR_NOT_A_MEMBER = "Not a project member"
ERR_OWNER_ONLY = "Owner only"
ERR_PROJECT_NOT_FOUND = "Project not found"
ERR_USER_NOT_FOUND = "User not found"
ERR_KEY_GENERATION_FAILED = "Could not generate a unique project key"
ERR_ALREADY_MEMBER = "User is already a member of this project"
ERR_AUTH_SERVICE_UNAVAILABLE = "User directory unavailable. Try again later."
ERR_SELF_TRANSFER = "Target is already the owner"
ERR_NOT_CURRENT_MEMBER = "Target is not a current member"
ERR_STORY_NOT_FOUND = "Story not found"
ERR_STORY_CREATE_STATUS = "Stories can only be created in backlog or todo status"
ERR_EPIC_NOT_IN_PROJECT = "Epic not found in this project"
ERR_NO_FIELDS_TO_UPDATE = "No fields to update"
ERR_INVALID_STATUS_TRANSITION = "Invalid status transition"
ERR_BACKLOG_REGRESSION = "Cannot move a committed story back to backlog"
ERR_ASSIGNEE_NOT_MEMBER = "Assignee must be a project member"
ERR_DELETE_FORBIDDEN = "You can only delete items you created"
ERR_STATUS_CHANGE_FORBIDDEN = "Only the assignee or the Owner can change this story's status"
ERR_SUBTASK_DEPTH = "Cannot create a subtask under another subtask"
ERR_COMMENT_EDIT_FORBIDDEN = "Only the comment author can edit this comment"
ERR_EPIC_NOT_FOUND = "Epic not found"
ERR_EPIC_EDIT_FORBIDDEN = "Only the epic reporter or project owner can edit this epic"
ERR_EPIC_DELETE_FORBIDDEN = "Only the epic reporter or project owner can delete this epic"
ERR_TASK_DELETE_FORBIDDEN = "Only the reporter or Owner can delete this task"
ERR_TASK_EDIT_FORBIDDEN = "Only the reporter or Owner can edit this task"
ERR_TASK_NOT_FOUND = "Task not found"
ERR_STORY_NOT_FOUND = "Story not found"
ERR_TASK_DONE_FORBIDDEN = "Only the assignee or Owner can toggle completion"
ERR_TASK_SUBTASKS_INCOMPLETE = "Cannot complete task: all subtasks must be done first"
ERR_INVALID_IMAGE_MIME = "Unsupported image type. Allowed: png, jpeg, gif, webp"
ERR_IMAGE_TOO_LARGE = "Image exceeds the 5 MB size limit"
