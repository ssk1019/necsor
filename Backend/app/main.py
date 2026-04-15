"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import get_settings
from app.core.database import close_mongodb, close_redis, connect_mongodb, connect_redis
from app.core.logging import setup_logging
from app.api.v1.router import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    # --- Startup ---
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} ({settings.APP_ENV})...")
    await connect_mongodb()
    await connect_redis()
    yield
    # --- Shutdown ---
    logger.info("Shutting down...")
    await close_redis()
    await close_mongodb()


def create_app() -> FastAPI:
    """Application factory."""
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

    # API routes
    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()
