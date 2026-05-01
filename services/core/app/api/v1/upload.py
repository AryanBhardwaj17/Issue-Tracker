"""
Upload router.

Endpoints
---------
POST /api/v1/upload/image  — validate and store an image; returns relative URL.
                             Requires a valid JWT; no project membership check.
"""

from fastapi import APIRouter, Depends, UploadFile, status

from app.api.deps import CurrentUser, get_current_user
from app.schemas.common import Envelope
from app.services import upload as upload_service

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post(
    "/image",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[dict],
)
async def upload_image(
    file: UploadFile,
    _user: CurrentUser = Depends(get_current_user),
) -> Envelope[dict]:
    """
    Upload a single image file and receive a relative URL to use in a comment.

    - **MIME allowlist:** image/png, image/jpeg, image/gif, image/webp
    - **Max size:** 5 MB
    - **Returns:** ``{ "url": "/uploads/<uuid>.<ext>" }``

    This endpoint has no project context. Call it first, then include the
    returned ``url`` in the JSON body of a comment create or edit request.
    """
    url = await upload_service.save_image(file)
    return Envelope(message="Image uploaded", data={"url": url})
