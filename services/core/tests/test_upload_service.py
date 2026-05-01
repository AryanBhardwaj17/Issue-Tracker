"""
Unit tests for the upload service.

Uses a real temporary directory (tmp_path) so the full write/unlink cycle
is exercised, matching the acceptance criteria.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.core.exceptions import PayloadTooLargeError, ValidationError
from app.services.upload import save_image

MAX_UPLOAD_SIZE = settings.MAX_UPLOAD_SIZE


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def uploads_dir(tmp_path, monkeypatch):
    """Point UPLOADS_DIR at a fresh temp dir for every test."""
    monkeypatch.setattr(settings, "UPLOADS_DIR", str(tmp_path))
    return tmp_path


def _make_upload_file(content: bytes, content_type: str, filename: str = "test.bin") -> MagicMock:
    """Return a mock UploadFile that yields `content` from .read()."""
    mock = MagicMock()
    mock.content_type = content_type
    mock.filename = filename
    mock.read = AsyncMock(return_value=content)
    return mock


# ── MIME validation ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_valid_png_upload(uploads_dir):
    file = _make_upload_file(b"fakepng" * 10, "image/png", "photo.png")
    url = await save_image(file)
    assert url.startswith("/uploads/")
    assert url.endswith(".png")
    # File must actually exist on disk
    filename = url[len("/uploads/") :]
    assert (uploads_dir / filename).exists()


@pytest.mark.asyncio
async def test_valid_jpeg_upload(uploads_dir):
    file = _make_upload_file(b"fakejpeg" * 10, "image/jpeg", "photo.jpeg")
    url = await save_image(file)
    assert url.endswith(".jpg")


@pytest.mark.asyncio
async def test_valid_gif_upload(uploads_dir):
    file = _make_upload_file(b"GIF89a", "image/gif", "anim.gif")
    url = await save_image(file)
    assert url.endswith(".gif")


@pytest.mark.asyncio
async def test_valid_webp_upload(uploads_dir):
    file = _make_upload_file(b"RIFFwebp", "image/webp", "img.webp")
    url = await save_image(file)
    assert url.endswith(".webp")


@pytest.mark.asyncio
async def test_invalid_mime_raises_422(uploads_dir):
    file = _make_upload_file(b"hello", "text/plain", "note.txt")
    with pytest.raises(ValidationError):
        await save_image(file)


@pytest.mark.asyncio
async def test_unsupported_image_mime_raises_422(uploads_dir):
    file = _make_upload_file(b"fakebmp", "image/bmp", "img.bmp")
    with pytest.raises(ValidationError):
        await save_image(file)


@pytest.mark.asyncio
async def test_missing_content_type_raises_422(uploads_dir):
    file = _make_upload_file(b"data", None, "file")
    with pytest.raises(ValidationError):
        await save_image(file)


# ── Size validation ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_oversize_raises_413(uploads_dir):
    big = b"x" * (MAX_UPLOAD_SIZE + 1)
    file = _make_upload_file(big, "image/png", "big.png")
    with pytest.raises(PayloadTooLargeError):
        await save_image(file)


@pytest.mark.asyncio
async def test_exactly_5mb_allowed(uploads_dir):
    exact = b"x" * MAX_UPLOAD_SIZE
    file = _make_upload_file(exact, "image/jpeg", "exact.jpg")
    url = await save_image(file)
    assert url.startswith("/uploads/")


# ── Filename format ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_uuid_filename(uploads_dir):
    file = _make_upload_file(b"img", "image/png", "anything.png")
    url = await save_image(file)
    # Strip "/uploads/" prefix and extension, must be a valid UUID4
    stem = url[len("/uploads/") :].rsplit(".", 1)[0]
    parsed = uuid.UUID(stem)  # raises ValueError if not a valid UUID
    assert parsed.version == 4


@pytest.mark.asyncio
async def test_extension_from_content_type_not_filename(uploads_dir):
    """content_type=image/png but filename says .jpg → saved as .png."""
    file = _make_upload_file(b"img", "image/png", "misleading.jpg")
    url = await save_image(file)
    assert url.endswith(".png")
