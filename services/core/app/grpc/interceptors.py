"""
Client-side gRPC interceptor that attaches the API key to every outbound call.
"""

from grpc import aio

from app.core.config import settings


class ApiKeyClientInterceptor(
    aio.UnaryUnaryClientInterceptor,
):
    """Inject ``x-api-key`` metadata into every outbound unary-unary RPC."""

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        metadata = list(client_call_details.metadata or [])
        metadata.append(("x-api-key", settings.INTERNAL_API_KEY))

        new_details = aio.ClientCallDetails(
            method=client_call_details.method,
            timeout=client_call_details.timeout,
            metadata=metadata,
            credentials=client_call_details.credentials,
            wait_for_ready=client_call_details.wait_for_ready,
        )
        return await continuation(new_details, request)
