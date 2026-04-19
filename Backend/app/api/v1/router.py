"""
API v1 router — aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, scheduler, market_data

api_router = APIRouter()

# 健康檢查
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# 排程管理
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["Scheduler"])

# 市場資料
api_router.include_router(market_data.router, prefix="/market", tags=["Market Data"])
