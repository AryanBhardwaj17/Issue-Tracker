"""
Async gRPC client for the Auth service's UserLookup RPC.

Usage::

    client = AuthGrpcClient()
    await client.connect()              # called at startup
    user = await client.get_user_by_email("alice@test.com")
    await client.close()                # called at shutdown
"""

import logging
import uuid
from dataclasses import dataclass

import grpc
from grpc import aio

from app.core.config import settings
from app.generated import user_lookup_pb2, user_lookup_pb2_grpc
from app.grpc.interceptors import ApiKeyClientInterceptor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthUser:
    """Lightweight value object returned by the gRPC client."""

    id: uuid.UUID
    name: str
    email: str


class AuthGrpcClient:
    """Thin async wrapper around the UserLookup gRPC channel."""

    def __init__(self) -> None:
        self._channel: aio.Channel | None = None
        self._stub: user_lookup_pb2_grpc.UserLookupStub | None = None

    async def connect(self) -> None:
        """Open the gRPC channel with the API-key interceptor."""
        interceptor = ApiKeyClientInterceptor()
        self._channel = aio.insecure_channel(
            settings.AUTH_SERVICE_GRPC_HOST,
            interceptors=[interceptor],
        )
        self._stub = user_lookup_pb2_grpc.UserLookupStub(self._channel)
        logger.info("gRPC channel opened to %s", settings.AUTH_SERVICE_GRPC_HOST)

    async def close(self) -> None:
        """Close the gRPC channel."""
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._stub = None
            logger.info("gRPC channel closed")

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        """Look up a user by email.  Returns ``None`` if not found."""
        assert self._stub is not None, "Client not connected"
        try:
            resp = await self._stub.GetUserByEmail(
                user_lookup_pb2.GetUserByEmailRequest(email=email),
                timeout=5,
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("gRPC GetUserByEmail failed: %s", exc)
            raise
        if not resp.found:
            return None
        return AuthUser(id=uuid.UUID(resp.id), name=resp.name, email=resp.email)

    async def get_users_by_ids(self, user_ids: list[uuid.UUID]) -> list[AuthUser]:
        """Bulk-fetch users by their UUIDs."""
        assert self._stub is not None, "Client not connected"
        try:
            resp = await self._stub.GetUsersByIds(
                user_lookup_pb2.GetUsersByIdsRequest(
                    user_ids=[str(uid) for uid in user_ids],
                ),
                timeout=5,
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("gRPC GetUsersByIds failed: %s", exc)
            raise
        return [AuthUser(id=uuid.UUID(u.id), name=u.name, email=u.email) for u in resp.users]
