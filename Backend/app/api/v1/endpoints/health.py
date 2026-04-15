"""
Health check endpoint.
"""

from fastapi import APIRouter
from loguru import logger

from app.core.database import get_database, get_redis

router = APIRouter()


@router.get("")
async def health_check():
    """Basic health check — verifies MongoDB and Redis connectivity."""
    status = {"status": "ok", "mongodb": "ok", "redis": "ok"}

    try:
        db = get_database()
        await db.command("ping")
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        status["mongodb"] = "error"
        status["status"] = "degraded"

    try:
        redis = get_redis()
        await redis.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        status["redis"] = "error"
        status["status"] = "degraded"

    return status
