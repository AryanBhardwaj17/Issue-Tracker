"""
Server-side gRPC interceptor that enforces API-key authentication.

Every inbound gRPC call must carry an ``x-api-key`` metadata entry whose
value matches ``settings.INTERNAL_API_KEY``.  Unauthenticated calls are
rejected with ``UNAUTHENTICATED``.
"""

import logging

import grpc
from grpc import aio

from app.core.config import settings

logger = logging.getLogger(__name__)


class ApiKeyInterceptor(aio.ServerInterceptor):
    """Validate the ``x-api-key`` metadata on every inbound RPC."""

    async def intercept_service(
        self,
        continuation,
        handler_call_details: grpc.HandlerCallDetails,
    ):
        metadata = dict(handler_call_details.invocation_metadata or [])
        api_key = metadata.get("x-api-key", "")

        if api_key != settings.INTERNAL_API_KEY:
            logger.warning(
                "gRPC auth failed for %s (ip=%s)",
                handler_call_details.method,
                metadata.get("peer", "unknown"),
            )

            async def _abort(request, context: grpc.aio.ServicerContext):
                await context.abort(
                    grpc.StatusCode.UNAUTHENTICATED,
                    "Invalid or missing API key",
                )

            return grpc.unary_unary_rpc_method_handler(_abort)

        return await continuation(handler_call_details)
