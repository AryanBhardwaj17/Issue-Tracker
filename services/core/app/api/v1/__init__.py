from fastapi import APIRouter

from app.api.v1 import (
    activity,
    comments,
    epic_comments,
    epics,
    members,
    projects,
    stories,
    subtasks,
    task_comments,
    tasks,
    trash,
    upload,
)

v1_router = APIRouter()
v1_router.include_router(projects.router)
v1_router.include_router(members.router)
v1_router.include_router(epics.router)
v1_router.include_router(stories.router)
v1_router.include_router(comments.router)
v1_router.include_router(task_comments.router)
v1_router.include_router(epic_comments.router)
v1_router.include_router(upload.router)
v1_router.include_router(tasks.router)
v1_router.include_router(subtasks.router)
v1_router.include_router(activity.router)
v1_router.include_router(trash.router)
