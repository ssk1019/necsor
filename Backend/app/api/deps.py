"""
Shared FastAPI dependencies (dependency injection).
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis

from app.core.database import get_database, get_redis


async def get_db() -> AsyncIOMotorDatabase:
    """Dependency: get MongoDB database instance."""
    return get_database()


async def get_cache() -> Redis:
    """Dependency: get Redis client instance."""
    return get_redis()
