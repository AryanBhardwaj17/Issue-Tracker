"""
Upload service — validates and persists image files to local disk.

Flow:
  1. Check MIME type against allowlist (ValidationError 422 on failure).
  2. Read all bytes and check size <= MAX_UPLOAD_SIZE (PayloadTooLargeError 413 on failure).
  3. Derive file extension from content-type (never from the original filename).
  4. Write to UPLOADS_DIR/<uuid4>.<ext> using aiofiles.
  5. Return relative URL string "/uploads/<uuid4>.<ext>".
"""

import logging
import os
import uuid

import aiofiles
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import PayloadTooLargeError, ValidationError
from app.utils.constants import ALLOWED_IMAGE_MIMES, MIME_TO_EXT

logger = logging.getLogger(__name__)


async def save_image(file: UploadFile) -> str:
    """
    Validate, store, and return the relative URL of the uploaded image.

    Raises:
        ValidationError (422): unsupported MIME type.
        PayloadTooLargeError (413): file exceeds the configured size limit.
    """
    # 1. MIME check — derive from content_type, never trust the filename extension
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_MIMES:
        raise ValidationError(
            f"Unsupported image type '{content_type}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_MIMES))}"
        )

    # 2. Read all bytes then check size
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE:
        raise PayloadTooLargeError()

    # 3. Derive extension from content-type
    ext = MIME_TO_EXT[content_type]

    # 4. Write to disk with a UUID filename
    filename = f"{uuid.uuid4()}{ext}"
    dest = os.path.join(settings.UPLOADS_DIR, filename)
    async with aiofiles.open(dest, "wb") as f:
        await f.write(data)

    logger.info("Image saved: %s (%d bytes)", dest, len(data))

    # 5. Return the relative URL path
    return f"/uploads/{filename}"
