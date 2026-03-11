from motor.motor_asyncio import AsyncIOMotorClient
from redis import asyncio as aioredis
from config import get_settings

settings = get_settings()

class Database:
    client: AsyncIOMotorClient = None
    db = None
    redis = None

    async def connect_db(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.redis = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        print("Connected to MongoDB and Redis")

    async def close_db(self):
        if self.client:
            self.client.close()
        if self.redis:
            await self.redis.close()
        print("Closed connections to MongoDB and Redis")

db = Database()
