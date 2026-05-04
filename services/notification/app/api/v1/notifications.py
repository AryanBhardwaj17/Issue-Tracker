"""Notification Service API — v1 endpoints."""

import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.core.database import get_db
from app.events.consumer import get_consumer_status, get_last_message_at
from app.schemas.notification import NotificationOut
from app.services import notification as notification_svc

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


@router.get("/")
async def list_notifications(
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return paginated notifications for the authenticated user."""
    notifications, total = await notification_svc.list_notifications(
        db, current_user.id, page=page, page_size=pageSize
    )
    return {
        "success": True,
        "message": "ok",
        "data": [NotificationOut.model_validate(n) for n in notifications],
        "pagination": {
            "page": page,
            "pageSize": pageSize,
            "total": total,
            "totalPages": max(1, math.ceil(total / pageSize)),
        },
    }


@router.get("/unread-count")
async def unread_count(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return number of unread notifications for the authenticated user."""
    count = await notification_svc.get_unread_count(db, current_user.id)
    return {
        "success": True,
        "message": "ok",
        "data": {"unreadCount": count},
    }


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark a single notification as read. 404 if not found, 403 if not yours."""
    notification = await notification_svc.mark_read(db, current_user.id, notification_id)
    return {
        "success": True,
        "message": "Notification marked as read",
        "data": NotificationOut.model_validate(notification),
    }


@router.post("/mark-all-read")
async def mark_all_read(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark all unread notifications for the authenticated user as read."""
    updated = await notification_svc.mark_all_read(db, current_user.id)
    return {
        "success": True,
        "message": "All notifications marked as read",
        "data": {"updatedCount": updated},
    }
