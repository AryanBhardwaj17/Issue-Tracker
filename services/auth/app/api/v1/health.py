"""Health-check endpoint for ALB / ECS."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    return {"status": "ok"}
