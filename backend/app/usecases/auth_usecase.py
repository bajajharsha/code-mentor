from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status

from app.models.domains.user import User, UserRole
from app.models.schema.user_schema import Token, UserCreate
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.utils.security_util import get_password_hash


class AuthUseCase:
    def __init__(
        self,
        user_repository: UserRepository = Depends(UserRepository),
        auth_service: AuthService = Depends(AuthService),
    ):
        self.user_repository = user_repository
        self.auth_service = auth_service

    async def register_user(self, user_data: UserCreate) -> Token:
        existing_email = await self.user_repository.get_user_by_email(user_data.email)
        if existing_email:
            raise ValueError("Email already registered")

        user_count = await self.user_repository.get_users_count()
        role = UserRole.ADMIN if user_count == 0 else UserRole.USER

        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            role=role,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        created_user = await self.user_repository.create_user(user)

        tokens = self.auth_service.create_tokens(
            email=created_user.get("email"),
            user_id=created_user.get("_id"),
            role=created_user.get("role"),
        )

        return tokens

    async def login_user(self, email: str, password: str) -> Optional[Token]:
        user = await self.auth_service.authenticate_user(email, password)
        if not user:
            return None

        tokens = self.auth_service.create_tokens(
            email=user.get("email"), user_id=user.get("_id"), role=user.get("role")
        )

        return tokens

    async def refresh_tokens(self, refresh_token: str) -> Token:
        return await self.auth_service.refresh_tokens(refresh_token)

    async def get_current_user_info(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing, access token missing",
            )

        parts = auth_header.split()
        if parts[0].lower() != "bearer" or len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format.",
            )
        access_token = parts[1]
        current_user = await self.auth_service.get_current_user(access_token)
        return current_user
