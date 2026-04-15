"""
Redis cache helper utilities.
"""

import json
from typing import Any

from app.core.database import get_redis


async def cache_get(key: str) -> Any | None:
    """Get a value from Redis cache (JSON-decoded)."""
    redis = get_redis()
    value = await redis.get(key)
    if value is None:
        return None
    return json.loads(value)


async def cache_set(key: str, value: Any, expire: int = 300) -> None:
    """Set a value in Redis cache (JSON-encoded). Default TTL: 300s."""
    redis = get_redis()
    await redis.set(key, json.dumps(value, default=str), ex=expire)


async def cache_delete(key: str) -> None:
    """Delete a key from Redis cache."""
    redis = get_redis()
    await redis.delete(key)
