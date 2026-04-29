from fastapi import APIRouter

from app.api.v1 import projects

v1_router = APIRouter()
v1_router.include_router(projects.router)
