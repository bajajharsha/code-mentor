from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

from app.config.settings import get_settings
from app.models.schema.user_schema import Token, TokenData
from app.repositories.user_repository import UserRepository
from app.utils.security_util import decode_token

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


class AuthService:
    def __init__(self, user_repository: UserRepository = Depends(UserRepository)):
        self.user_repository = user_repository

    async def authenticate_user(self, email: str, password: str):
        from app.utils.security_util import verify_password

        user = await self.user_repository.get_user_by_email(email)
        if not user:
            return False
        if not verify_password(password, user.get("hashed_password")):
            return False
        return user

    def create_tokens(self, email: str, user_id: str, role: str) -> Token:
        from app.utils.security_util import create_access_token, create_refresh_token

        token_data = {"sub": email, "_id": user_id, "role": role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            role=role,
        )

    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:

            payload = decode_token(token)
            email: str = payload.get("sub")  # email
            user_id: str = payload.get("_id")
            token_type: str = payload.get("type")

            if email is None or user_id is None:
                raise credentials_exception
            if token_type != "access":
                raise credentials_exception

            token_data = TokenData(email=email, user_id=user_id)
        except JWTError:
            raise credentials_exception

        user = await self.user_repository.get_user_by_email(token_data.email)
        if user is None:
            raise credentials_exception

        return user

    async def refresh_tokens(self, refresh_token: str) -> Token:
        try:
            payload = decode_token(refresh_token)
            email: str = payload.get("sub")
            user_id: str = payload.get("_id")
            token_type: str = payload.get("type")

            if email is None or user_id is None or token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            user = await self.user_repository.get_user_by_email(email)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

            return self.create_tokens(email, user_id, user.get("role"))

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh Token expired.",
            )
        except JWTClaimsError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has invalid claims.",
            )

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )