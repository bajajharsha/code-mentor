from datetime import datetime, timezone
from enum import Enum

from bson import ObjectId


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User:
    def __init__(
        self,
        email: str,
        hashed_password: str,
        role: UserRole = UserRole.USER,
        disabled: bool = False,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self._id = ObjectId()
        self.email = email
        self.hashed_password = hashed_password
        self.role = role
        self.disabled = disabled
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @classmethod
    def from_dict(cls, data: dict):
        if "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)

    def to_dict(self):
        return {
            "_id": str(self._id),
            "email": self.email,
            "hashed_password": self.hashed_password,
            "role": self.role,
            "disabled": self.disabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
