"""
API v1 router — aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, scheduler

api_router = APIRouter()

# 健康檢查
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# 排程管理
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["Scheduler"])

# Add more routers here as the project grows, e.g.:
# from app.api.v1.endpoints import users, items
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(items.router, prefix="/items", tags=["Items"])
