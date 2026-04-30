"""
UserLookup gRPC servicer — resolves users by email or by IDs.

This servicer creates its own DB sessions (via ``AsyncSessionLocal``) because
gRPC handlers run outside the FastAPI dependency-injection lifecycle.
"""

import logging
import uuid

from app.core.database import AsyncSessionLocal
from app.generated import user_lookup_pb2, user_lookup_pb2_grpc
from app.repositories import user as user_repo

logger = logging.getLogger(__name__)


class UserLookupServicer(user_lookup_pb2_grpc.UserLookupServicer):
    """Implements the ``UserLookup`` gRPC service defined in user_lookup.proto."""

    async def GetUserByEmail(self, request, context):
        """Look up a single user by email address."""
        email = request.email.strip().lower()
        logger.debug("GetUserByEmail called: email=%s", email)

        async with AsyncSessionLocal() as db:
            user = await user_repo.get_user_by_email(db, email)

        if user is None:
            return user_lookup_pb2.UserResponse(found=False)

        return user_lookup_pb2.UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            found=True,
        )

    async def GetUsersByIds(self, request, context):
        """Bulk-fetch users by a list of UUIDs."""
        raw_ids = list(request.user_ids)
        logger.debug("GetUsersByIds called: count=%d", len(raw_ids))

        # Parse valid UUIDs and silently skip malformed ones.
        valid_ids: list[uuid.UUID] = []
        for raw in raw_ids:
            try:
                valid_ids.append(uuid.UUID(raw))
            except ValueError:
                logger.warning("Skipping malformed UUID: %s", raw)

        if not valid_ids:
            return user_lookup_pb2.UsersResponse(users=[])

        async with AsyncSessionLocal() as db:
            users = await user_repo.get_users_by_ids(db, valid_ids)

        return user_lookup_pb2.UsersResponse(
            users=[
                user_lookup_pb2.UserInfo(
                    id=str(u.id),
                    name=u.name,
                    email=u.email,
                )
                for u in users
            ],
        )
