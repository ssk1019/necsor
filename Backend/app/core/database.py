"""
Database connection management for MongoDB and Redis.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import ConnectionPool, Redis
from loguru import logger

from app.core.config import get_settings

settings = get_settings()

# --- MongoDB ---

_mongo_client: AsyncIOMotorClient | None = None
_mongo_db: AsyncIOMotorDatabase | None = None


async def connect_mongodb() -> None:
    """Establish MongoDB connection."""
    global _mongo_client, _mongo_db
    logger.info("Connecting to MongoDB...")
    _mongo_client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        maxPoolSize=50,
        minPoolSize=10,
    )
    _mongo_db = _mongo_client[settings.MONGODB_DB_NAME]
    # Verify connection
    await _mongo_client.admin.command("ping")
    logger.info("MongoDB connected successfully.")


async def close_mongodb() -> None:
    """Close MongoDB connection."""
    global _mongo_client, _mongo_db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    """Get the MongoDB database instance."""
    if _mongo_db is None:
        raise RuntimeError("MongoDB is not connected.")
    return _mongo_db


# --- Redis ---

_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None


async def connect_redis() -> None:
    """Establish Redis connection pool."""
    global _redis_pool, _redis_client
    logger.info("Connecting to Redis...")
    _redis_pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        password=settings.REDIS_PASSWORD or None,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=True,
    )
    _redis_client = Redis(connection_pool=_redis_pool)
    # Verify connection
    await _redis_client.ping()
    logger.info("Redis connected successfully.")


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _redis_pool, _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection closed.")


def get_redis() -> Redis:
    """Get the Redis client instance."""
    if _redis_client is None:
        raise RuntimeError("Redis is not connected.")
    return _redis_client
