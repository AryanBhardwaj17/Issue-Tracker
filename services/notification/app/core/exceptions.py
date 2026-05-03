"""Domain exception hierarchy for the Notification Service."""

from app.utils.constants import (
    ERR_FORBIDDEN,
    ERR_INVALID_TOKEN,
    ERR_NOT_FOUND,
    ERR_NOT_YOUR_NOTIFICATION,
)


class AppException(Exception):
    """Base class for all Notification Service domain exceptions."""

    status_code: int = 500
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class InvalidTokenError(AppException):
    """Raised when a JWT is missing, malformed, expired, or has a bad signature."""

    status_code = 401
    detail = ERR_INVALID_TOKEN


class ForbiddenError(AppException):
    """Raised when the caller is authenticated but not authorised."""

    status_code = 403
    detail = ERR_FORBIDDEN


class NotFoundError(AppException):
    """Raised when a resource does not exist."""

    status_code = 404
    detail = ERR_NOT_FOUND


class NotYourNotificationError(AppException):
    """Raised when a user tries to access another user's notification."""

    status_code = 403
    detail = ERR_NOT_YOUR_NOTIFICATION
