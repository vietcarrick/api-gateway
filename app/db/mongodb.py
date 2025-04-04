from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


class MongoDB:
    client: AsyncIOMotorClient = None


mongodb = MongoDB()


async def get_mongodb():
    return mongodb.client[settings.MONGODB_DB]


async def connect_to_mongo():
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)


async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()