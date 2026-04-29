"""
User service — business logic for profile management and password changes.
 
All functions work with ORM model instances passed in from the API layer
(via the ``get_current_user`` dependency) so no extra DB lookup is needed
for the authenticated user.
"""
 
import logging
from uuid import UUID
 
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.core.exceptions import (
    UserNotFoundError,
    WrongPasswordError,
)
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import token as token_repo
from app.repositories import user as user_repo
 
logger = logging.getLogger(__name__)
 
 
async def get_profile(db: AsyncSession, *, user_id: UUID) -> User:
    """Return the user with ``user_id``.
 
    Raises:
        UserNotFoundError: If no user exists with that id.
    """
    user = await user_repo.get_user_by_id(db, user_id)
    if not user:
        raise UserNotFoundError()
    return user

 
async def change_password(
    db: AsyncSession,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    """Update the user's password and revoke all existing refresh tokens.
 
    Revoking tokens forces all other active sessions to re-authenticate,
    which is the expected behaviour after a password change.
 
    Raises:
        WrongPasswordError: If ``current_password`` does not match the stored hash.
    """
    if not verify_password(current_password, user.password_hash):
        raise WrongPasswordError()
 
    await user_repo.update_user(db, user, password_hash=hash_password(new_password))
    revoked = await token_repo.revoke_all_user_tokens(db, user.id)
    logger.info("Password changed for user_id=%s — %s session(s) revoked", user.id, revoked)
 
 