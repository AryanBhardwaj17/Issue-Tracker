"""ORM model registry — import all models so Alembic can detect them."""

from app.models.notification import DeliveryStatus, EmailDelivery, Notification

__all__ = [
    "DeliveryStatus",
    "EmailDelivery",
    "Notification",
]
