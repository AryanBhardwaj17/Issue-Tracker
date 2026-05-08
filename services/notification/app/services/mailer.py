"""Email sending wrapper over FastAPI-Mail."""

import logging

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings

logger = logging.getLogger(__name__)

_conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USERNAME,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.SMTP_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_STARTTLS=settings.SMTP_USE_TLS,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=bool(settings.SMTP_USERNAME),
    VALIDATE_CERTS=settings.SMTP_VALIDATE_CERTS,
)

_mail = FastMail(_conf)


async def send_email(to: str, subject: str, html: str) -> None:
    """
    Send an HTML email to a single recipient.

    Raises on SMTP failure — callers must catch and handle
    (update EmailDelivery status to FAILED).
    """
    msg = MessageSchema(
        subject=subject,
        recipients=[to],
        body=html,
        subtype=MessageType.html,
    )
    await _mail.send_message(msg)
    logger.info("Email sent to=%s subject=%r", to, subject)
