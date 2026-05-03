"""Notification Service API — v1 endpoints."""

from datetime import datetime

from fastapi import APIRouter

from app.events.consumer import get_consumer_status, get_last_message_at

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Consumer liveness check. Returns consumer connection state and last-message timestamp."""
    last_msg: datetime | None = get_last_message_at()
    return {
        "success": True,
        "message": "ok",
        "data": {
            "consumer": get_consumer_status(),
            "last_message_at": last_msg.isoformat() if last_msg else None,
        },
    }
