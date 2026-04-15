"""
API v1 router — aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()

# Health check
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# Add more routers here as the project grows, e.g.:
# from app.api.v1.endpoints import users, items
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(items.router, prefix="/items", tags=["Items"])
