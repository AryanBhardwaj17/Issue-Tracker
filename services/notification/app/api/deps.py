"""FastAPI dependency functions — JWT verification."""

import uuid
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.exceptions import InvalidTokenError
from app.core.security import decode_access_token


@dataclass
class CurrentUser:
    """Caller identity extracted from the verified JWT payload."""

    id: uuid.UUID
    name: str
    email: str


_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    """Extract and verify the RS256 JWT from the Authorization header."""
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise InvalidTokenError()

    try:
        user_id = uuid.UUID(payload["sub"])
        name: str = payload["name"]
        email: str = payload["email"]
    except (KeyError, ValueError):
        raise InvalidTokenError()

    return CurrentUser(id=user_id, name=name, email=email)
