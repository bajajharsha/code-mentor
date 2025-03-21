from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.repositories.user_repository import UserRepository

from app.config.settings import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.now((timezone.utc)) + expires_delta #now((datetime.timezone.utc)) .utcnow()
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )

def create_access_token(data: dict) -> str:
    print(f"minutes :  {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    return create_token(
        data=data, 
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access"
    )

def create_refresh_token(data: dict) -> str:
    print(f"creating refresh token")
    return create_token(
        data=data, 
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh"
    )

def decode_token(token: str) -> dict:
    return jwt.decode(
        token, 
        settings.JWT_SECRET_KEY, 
        algorithms=[settings.JWT_ALGORITHM]
    )

async def get_current_user(token: str = Depends(oauth2_scheme), user_repository :UserRepository = Depends(UserRepository)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        
        try:
            # token = token.strip()
            
            payload = decode_token(token)

            email: str = payload.get("sub") #email
            user_id: str = payload.get("_id")
            token_type: str = payload.get("type")
            
            if email is None or user_id is None:
                raise credentials_exception
            if token_type != "access":
                raise credentials_exception
                
            token_data = {
                "email": email,
                "user_id": user_id
            }
            # token_data = TokenData(email=email, user_id=user_id)
        except JWTError:
            raise credentials_exception
        
        # user_repository = UserRepository()
        user = await user_repository.get_user_by_email(token_data.get("email"))
        if user is None:
            raise credentials_exception
        
        return user