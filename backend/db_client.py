import os
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

class MongoDBClient:
    """Singleton MongoDB client"""
    _instance = None
    _sync_client: Optional[pymongo.MongoClient] = None
    _async_client: Optional[AsyncIOMotorClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.mongodb_url = os.getenv(
            "MONGODB_URL", 
            "mongodb://admin:pass1234@localhost:27017/production?authSource=admin"
        )
    
    def get_sync_client(self) -> pymongo.MongoClient:
        if self._sync_client is None:
            self._sync_client = pymongo.MongoClient(self.mongodb_url)
        return self._sync_client
    
    def get_async_client(self) -> AsyncIOMotorClient:
        if self._async_client is None:
            self._async_client = AsyncIOMotorClient(self.mongodb_url)
        return self._async_client
    
    def get_sync_db(self):
        return self.get_sync_client().production
    
    def get_async_db(self):
        return self.get_async_client().production
    
    def close_connections(self):
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        if self._async_client:
            self._async_client.close()
            self._async_client = None

# Global instance
mongo_client = MongoDBClient()