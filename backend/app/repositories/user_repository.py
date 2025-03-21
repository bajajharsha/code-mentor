from typing import Optional

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_db
from app.models.domains.user import User


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase = Depends(get_db)):
        self.db = db
        self.collection = self.db.users

    async def create_user(self, user: User) -> User:
        user_dict = user.to_dict()
        result = await self.collection.insert_one(user_dict)
        return user_dict

    async def get_user_by_username(self, username: str) -> Optional[User]:
        user_data = await self.collection.find_one({"username": username})
        if user_data:
            return user_data
        return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        user_data = await self.collection.find_one({"email": email})
        if user_data:
            return user_data
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        from bson import ObjectId

        user_data = await self.collection.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return user_data
        return None

    async def update_user(self, user: User) -> User:
        from bson import ObjectId

        user_dict = user.to_dict()
        await self.collection.update_one(
            {"_id": ObjectId(user.id)}, {"$set": user_dict}
        )
        return user

    async def get_users_count(self) -> int:
        return await self.collection.count_documents({})
