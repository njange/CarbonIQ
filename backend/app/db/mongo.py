from motor.motor_asyncio import AsyncIOMotorClient
from . import mongo
from app.code.config import settings

_client: AsyncIOMotorClient | None = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if not _client:
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
    return _client

def get_db():
    return get_client()[settings.MONGODB_DB]