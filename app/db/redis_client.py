from redis.asyncio import Redis
from app.core.config import settings


class RedisClient:
    def __init__(self):
        self.client = None

    async def connect(self):
        self.client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

    async def close(self):
        if self.client:
            await self.client.close()


redis_client = RedisClient()
