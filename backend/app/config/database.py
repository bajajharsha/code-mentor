from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import get_settings

settings = get_settings()

class Database:
    client: AsyncIOMotorClient = None
    def __init__(self):
        self.client: AsyncIOMotorClient = None

    async def connect(self):
        try:
            if self.client is None:
                self.client = AsyncIOMotorClient(
                    settings.MONGODB_URL,
                    maxPoolSize=1000,
                    minPoolSize=50,
                    maxIdleTimeMS=50000,
                    connectTimeoutMS=20000,
                )

                self.db = self.client[settings.DB_NAME]
                await self.client.admin.command("ping")

        except Exception as e:
            if self.client:
                await self.disconnect()
            raise

    async def get_db(self):
        if self.client is None:
            await self.connect()
        return self.client[settings.DB_NAME]

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

db = Database()
async def get_db():
    return await db.get_db()

async def connect_to_mongodb():
    return db.connect()
    
async def close_mongodb_connection():
    return db.disconnect()