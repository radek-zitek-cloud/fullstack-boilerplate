from fastapi import APIRouter

from app.api.api_v1.endpoints import admin_rbac, audit, auth, tasks, trash, uploads, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(audit.router, tags=["audit"])
api_router.include_router(trash.router, tags=["trash"])
api_router.include_router(admin_rbac.router, tags=["admin-rbac"])
