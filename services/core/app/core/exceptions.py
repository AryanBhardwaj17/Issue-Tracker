"""
Domain exception hierarchy for the Core Service.

All exceptions inherit from ``AppException`` so the global exception handler
in ``main.py`` can catch them in one place and map them to HTTP responses.

Error message strings are imported from ``utils.constants`` — the single
source of truth — so they never diverge between exceptions and API responses.
"""

from app.utils.constants import (
    ERR_ALREADY_MEMBER,
    ERR_AUTH_SERVICE_UNAVAILABLE,
    ERR_COMMENT_NOT_FOUND,
    ERR_EPIC_DELETE_FORBIDDEN,
    ERR_EPIC_EDIT_FORBIDDEN,
    ERR_EPIC_NOT_FOUND,
    ERR_IMAGE_TOO_LARGE,
    ERR_INVALID_TOKEN,
    ERR_KEY_GENERATION_FAILED,
    ERR_NOT_A_MEMBER,
    ERR_PROJECT_NOT_FOUND,
    ERR_STORY_NOT_FOUND,
    ERR_TASK_NOT_FOUND,
    ERR_USER_NOT_FOUND,
)


class AppException(Exception):
    """Base class for all Core Service domain exceptions."""

    status_code: int = 500
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


# ── 401 Unauthorized ───────────────────────────────────────────────────────────────


class InvalidTokenError(AppException):
    """Raised when a JWT is missing, malformed, expired, or has a bad signature."""

    status_code = 401
    detail = ERR_INVALID_TOKEN


# ── 403 Forbidden ───────────────────────────────────────────────────────────────


class ForbiddenError(AppException):
    """Raised when the caller is authenticated but not authorised."""

    status_code = 403
    detail = ERR_NOT_A_MEMBER


# ── 404 Not Found ───────────────────────────────────────────────────────────────


class ProjectNotFoundError(AppException):
    """Raised when a project does not exist or has been soft-deleted."""

    status_code = 404
    detail = ERR_PROJECT_NOT_FOUND


# ── 400 Bad Request ───────────────────────────────────────────────────────────────


class EpicNotFoundError(AppException):
    """Raised when an epic does not exist or has been soft-deleted."""

    status_code = 404
    detail = ERR_EPIC_NOT_FOUND


class EpicEditForbiddenError(AppException):
    """Raised when a member tries to edit an epic they did not create."""

    status_code = 403
    detail = ERR_EPIC_EDIT_FORBIDDEN


class EpicDeleteForbiddenError(AppException):
    """Raised when a member tries to delete an epic they did not create."""

    status_code = 403
    detail = ERR_EPIC_DELETE_FORBIDDEN


class BadRequestError(AppException):
    """Raised for invalid business logic requests (e.g. self-transfer)."""

    status_code = 400
    detail = "Bad request"


# ── 409 Conflict ───────────────────────────────────────────────────────────────


class KeyGenerationError(AppException):
    """Raised when a unique project key could not be generated after retries."""

    status_code = 409
    detail = ERR_KEY_GENERATION_FAILED


class AlreadyMemberError(AppException):
    """Raised when a user is already a member of the project."""

    status_code = 409
    detail = ERR_ALREADY_MEMBER


class UserNotFoundError(AppException):
    """Raised when a user lookup returns no result."""

    status_code = 404
    detail = ERR_USER_NOT_FOUND


class AuthServiceUnavailableError(AppException):
    """Raised when the Auth gRPC service cannot be reached."""

    status_code = 503
    detail = ERR_AUTH_SERVICE_UNAVAILABLE


# ── 404 Not Found (Domain entities) ──────────────────────────────────────────


class TaskNotFoundError(AppException):
    """Raised when a task does not exist or has been soft-deleted."""

    status_code = 404
    detail = ERR_TASK_NOT_FOUND


class StoryNotFoundError(AppException):
    """Raised when a story does not exist or has been soft-deleted."""

    status_code = 404
    detail = ERR_STORY_NOT_FOUND


class CommentNotFoundError(AppException):
    """Raised when a comment does not exist or has been soft-deleted."""

    status_code = 404
    detail = ERR_COMMENT_NOT_FOUND


# ── 413 Payload Too Large ──────────────────────────────────────────────────────


class PayloadTooLargeError(AppException):
    """Raised when an uploaded file exceeds the size limit."""

    status_code = 413
    detail = ERR_IMAGE_TOO_LARGE


# ── 422 Validation ─────────────────────────────────────────────────────────────


class ValidationError(AppException):
    """Raised for field-level validation failures (422)."""

    status_code = 422