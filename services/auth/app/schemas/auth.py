"""
Pydantic schemas for authentication request/response payloads.

Validation constraints (lengths, pattern) are imported from ``utils.constants``
so they stay in sync with the ORM model column definitions.
"""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse
from app.utils.constants import (
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    TOKEN_TYPE_BEARER,
)

class RegisterRequest(BaseModel):
    """Payload for POST /auth/signup."""

    name: str = Field(..., min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    email: EmailStr
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr
    password: str

class AccessTokenResponse(BaseModel):
    """Returned after a token refresh — only the new access token in the body."""

    access_token: str
    token_type: str = TOKEN_TYPE_BEARER


class AuthResponse(BaseModel):
    """Returned after signup and login — user profile plus tokens."""

    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = TOKEN_TYPE_BEARER
