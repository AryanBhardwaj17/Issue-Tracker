"""
User profile routes — read, update, change password.
 
All endpoints require a valid JWT bearer token.  The authenticated user is
injected via ``get_current_user``, so only "self" operations are possible
(no admin viewing other profiles).
"""
 
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services import user as user_service
 
router = APIRouter(prefix="/users", tags=["Users"])
 
 
@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the authenticated user's profile."""
    return current_user  # type: ignore[return-value]
 
 
@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Change the authenticated user's password and revoke all sessions."""
    await user_service.change_password(
        db,
        user=current_user,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return MessageResponse(message="Password changed — all sessions revoked")
 
 