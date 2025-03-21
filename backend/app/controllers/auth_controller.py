from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, Response, status

from app.models.schema.user_schema import Token, UserCreate
from app.usecases.auth_usecase import AuthUseCase
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.config.database import get_db

from app.config.settings import get_settings

settings = get_settings()

class AuthController:
    def __init__(self, auth_usecase: AuthUseCase = Depends(AuthUseCase)):
        self.auth_usecase = auth_usecase

    async def register(self, user_data: UserCreate) -> Token:
        try:
            tokens = await self.auth_usecase.register_user(user_data)
            return tokens
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def login(self, email: str, password: str, response: Response) -> Token:
        tokens = await self.auth_usecase.login_user(email, password)
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure = True,
            samesite="strict",
            max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
            path="/api/v1/auth/refresh-token"
        )

        return Token(
            access_token=tokens.access_token,
            refresh_token="",
            token_type="bearer",
            role=tokens.role,
        )

    async def refresh(self, refresh_token: Optional[str] = Cookie(None)) -> Token:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing",
            )

        try:
            return await self.auth_usecase.refresh_tokens(refresh_token)
        except HTTPException as e:
            raise e

    async def get_current_user_info(self, request: Request):
        return await self.auth_usecase.get_current_user_info(request)
