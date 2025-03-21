from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    role: UserRole
    disabled: bool = False
    created_at: datetime
    updated_at: datetime


class UserInDB(UserBase):
    hashed_password: str
    role: UserRole
    disabled: bool = False
    created_at: datetime
    updated_at: datetime


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str
    role: str
