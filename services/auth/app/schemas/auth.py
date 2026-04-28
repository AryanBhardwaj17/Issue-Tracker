"""
Pydantic schemas for authentication request/response payloads.

Validation constraints (lengths, pattern) are imported from ``utils.constants``
so they stay in sync with the ORM model column definitions.
"""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserResponse
from app.utils.constants import (
    ERR_WEAK_PASSWORD,
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    PASSWORD_REGEX,
    TOKEN_TYPE_BEARER,
)


class RegisterRequest(BaseModel):
    """Payload for POST /auth/signup."""

    name: str = Field(..., min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    email: EmailStr
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.fullmatch(PASSWORD_REGEX, v):
            raise ValueError(ERR_WEAK_PASSWORD)
        return v


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
