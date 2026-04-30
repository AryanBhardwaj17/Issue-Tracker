from fastapi import APIRouter

from app.api.v1 import members, projects

v1_router = APIRouter()
v1_router.include_router(projects.router)
v1_router.include_router(members.router)
