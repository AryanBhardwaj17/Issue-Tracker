"""
FastAPI dependencies for the API layer.

``get_current_user`` extracts and verifies the JWT from the ``Authorization``
header and returns the authenticated ``User`` ORM instance.  All protected
routes should declare ``current_user: User = Depends(get_current_user)``.
"""

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import InvalidAccessTokenError
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories import user as user_repo

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the JWT bearer token and return the authenticated user.

    Steps:
        1. Ensure a bearer token was provided.
        2. Decode and verify the RS256 signature + expiry.
        3. Extract the ``sub`` claim (user id).
        4. Fetch the user from the database.
        5. Return the ORM instance, or raise ``InvalidAccessTokenError``.

    Raises:
        InvalidAccessTokenError: On missing / malformed / expired token, or if
            the user id in ``sub`` does not correspond to an existing account.
    """
    if credentials is None:
        raise InvalidAccessTokenError()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise InvalidAccessTokenError() from exc

    user = await user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise InvalidAccessTokenError()

    return user
