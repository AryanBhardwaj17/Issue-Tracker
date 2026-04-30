"""
gRPC server bootstrap for the auth service.

Provides ``start_grpc_server`` / ``stop_grpc_server`` helpers called from
``main.py``'s lifespan.  The server only starts when ``INTERNAL_API_KEY``
is configured (non-empty) — this keeps existing dev/test flows working
where no gRPC is needed.
"""

import logging

from grpc import aio

from app.core.config import settings
from app.generated import user_lookup_pb2_grpc
from app.grpc.interceptors import ApiKeyInterceptor
from app.grpc.servicers.user_lookup import UserLookupServicer

logger = logging.getLogger(__name__)

_server: aio.Server | None = None


async def start_grpc_server() -> None:
    """Create, configure, and start the gRPC server."""
    global _server  # noqa: PLW0603

    if not settings.INTERNAL_API_KEY:
        logger.info("INTERNAL_API_KEY is empty — gRPC server will NOT start")
        return

    _server = aio.server(interceptors=[ApiKeyInterceptor()])
    user_lookup_pb2_grpc.add_UserLookupServicer_to_server(
        UserLookupServicer(), _server,
    )

    listen_addr = f"[::]:{settings.GRPC_PORT}"
    _server.add_insecure_port(listen_addr)
    await _server.start()
    logger.info("gRPC server listening on %s", listen_addr)


async def stop_grpc_server() -> None:
    """Gracefully shut down the gRPC server (if running)."""
    global _server  # noqa: PLW0603

    if _server is None:
        return

    logger.info("Shutting down gRPC server...")
    await _server.stop(grace=5)
    _server = None
    logger.info("gRPC server stopped")
