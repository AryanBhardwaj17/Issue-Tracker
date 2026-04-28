"""
Domain exception hierarchy for the auth service.

All exceptions inherit from ``AppException`` so the global exception handler
in ``main.py`` can catch them in one place and map them to HTTP responses.

Error message strings are imported from ``utils.constants`` — the single
source of truth — so they never diverge between exceptions and API responses.
"""

from app.utils.constants import (
    ERR_EMAIL_REGISTERED,
    ERR_INVALID_ACCESS_TOKEN,
    ERR_INVALID_CREDENTIALS,
    ERR_INVALID_REFRESH_TOKEN,
    ERR_NAME_GENERATION_FAILED,
    ERR_USER_NOT_FOUND,
    ERR_USER_UNAVAILABLE,
    ERR_WRONG_PASSWORD,
)


class AppException(Exception):
    """Base class for all auth-service domain exceptions.

    Subclasses set ``status_code`` and ``detail`` as class attributes so
    they can be raised with zero arguments and still carry the correct HTTP
    status and message.  Pass a ``detail`` string to override the default.
    """

    status_code: int = 500
    detail: str = "An unexpected error occurred"
    headers: dict | None = None

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


# ── 409 Conflict ──────────────────────────────────────────────────────────────


class NameGenerationError(AppException):
    """Raised when a unique display name could not be generated after retries."""

    status_code = 409
    detail = ERR_NAME_GENERATION_FAILED


class EmailAlreadyRegisteredError(AppException):
    """Raised when a requested email address is already registered."""

    status_code = 409
    detail = ERR_EMAIL_REGISTERED


# ── 401 Unauthorized ──────────────────────────────────────────────────────────


class InvalidCredentialsError(AppException):
    """Raised on login when the email/password combination is incorrect."""

    status_code = 401
    detail = ERR_INVALID_CREDENTIALS


class InvalidRefreshTokenError(AppException):
    """Raised when a refresh token is missing, revoked, or expired."""

    status_code = 401
    detail = ERR_INVALID_REFRESH_TOKEN


class UserUnavailableError(AppException):
    """Raised during token refresh when the owning user no longer exists."""

    status_code = 401
    detail = ERR_USER_UNAVAILABLE


class InvalidAccessTokenError(AppException):
    """Raised when the JWT bearer token is absent, expired, or has an invalid signature."""

    status_code = 401
    detail = ERR_INVALID_ACCESS_TOKEN
    headers = {"WWW-Authenticate": "Bearer"}


# ── 404 Not Found ─────────────────────────────────────────────────────────────


class UserNotFoundError(AppException):
    """Raised when a user lookup by id returns no result."""

    status_code = 404
    detail = ERR_USER_NOT_FOUND


# ── 400 Bad Request ───────────────────────────────────────────────────────────


class WrongPasswordError(AppException):
    """Raised during password-change when the supplied current password is incorrect."""

    status_code = 400
    detail = ERR_WRONG_PASSWORD
