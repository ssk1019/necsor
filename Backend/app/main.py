"""
FastAPI 應用程式入口。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import get_settings
from app.core.database import (
    close_mongodb, close_redis, connect_mongodb, connect_redis, get_database,
)
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.models.daily_market import ensure_daily_market_indexes
from app.models.twse_institutional import ensure_twse_institutional_indexes
from app.models.tpex_institutional import ensure_tpex_institutional_indexes
from app.models.margin_trading import ensure_margin_trading_indexes
from app.models.futures_oi import ensure_futures_oi_indexes
from app.models.futures_institutional import ensure_futures_institutional_indexes
from app.scheduler.engine import SchedulerEngine

settings = get_settings()

# 排程引擎全域實例
_scheduler: SchedulerEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式啟動 / 關閉生命週期。"""
    global _scheduler

    # --- 啟動 ---
    setup_logging()
    logger.info(f"啟動 {settings.APP_NAME} ({settings.APP_ENV})...")
    await connect_mongodb()
    await connect_redis()

    # 建立 MongoDB 索引
    await ensure_daily_market_indexes(get_database())
    await ensure_twse_institutional_indexes(get_database())
    await ensure_tpex_institutional_indexes(get_database())
    await ensure_margin_trading_indexes(get_database())
    await ensure_futures_oi_indexes(get_database())
    await ensure_futures_institutional_indexes(get_database())

    # 載入任務模組（觸發 @register_task 裝飾器）
    import app.scheduler.tasks  # noqa: F401

    # 啟動排程引擎
    _scheduler = SchedulerEngine(get_database())
    await _scheduler.start()

    yield

    # --- 關閉 ---
    logger.info("正在關閉...")
    if _scheduler:
        await _scheduler.stop()
    await close_redis()
    await close_mongodb()


def create_app() -> FastAPI:
    """應用程式工廠。"""
    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API 路由
    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()
