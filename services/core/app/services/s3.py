"""S3 upload helper — used only when USE_S3=True."""

import logging
import uuid

import boto3
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import PayloadTooLargeError, ValidationError
from app.utils.constants import ALLOWED_IMAGE_MIMES, MIME_TO_EXT

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("s3", region_name=settings.S3_REGION)
    return _client


async def save_image_s3(file: UploadFile) -> str:
    """
    Validate, upload to S3, and return the public URL.

    Uses the same validation logic as the local upload service.
    """
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_MIMES:
        raise ValidationError(
            f"Unsupported image type '{content_type}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_MIMES))}"
        )

    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE:
        raise PayloadTooLargeError()

    ext = MIME_TO_EXT[content_type]
    key = f"uploads/{uuid.uuid4()}{ext}"

    client = _get_client()
    client.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )

    url = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{key}"
    logger.info("Image uploaded to S3: %s (%d bytes)", key, len(data))
    return url
