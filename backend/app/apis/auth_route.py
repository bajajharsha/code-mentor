from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from app.utils.error_handler_decorator import handle_exceptions
from app.controllers.auth_controller import AuthController
from app.models.schema.user_schema import Token, UserCreate
from app.utils.security_util import get_current_user

from app.config.settings import get_settings
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=Token)
@handle_exceptions
async def register(
    user_data: UserCreate, auth_controller: AuthController = Depends(AuthController)
):
    result = await auth_controller.register(user_data)
    return JSONResponse(
        content={
            "data": {
                "access_token": result.access_token,
                "refresh_token": result.refresh_token,
                "token_type": result.token_type,
                "role": result.role,
            },
            "statuscode": 200,
            "detail": "user registered successfully",
            "error": "",
        },
        status_code=status.HTTP_200_OK,
    )


@router.post("/login", response_model=Token)
@handle_exceptions
async def login(
    login_request: UserCreate,  # form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    auth_controller: AuthController = Depends(AuthController),
):
    result = await auth_controller.login(
        email=login_request.email, password=login_request.password, response=response
    )
    return result

@router.post("/refresh-token", response_model=Token)
@handle_exceptions
async def refresh_token(
    request: Request,
    response: Response,
    auth_controller: AuthController = Depends(AuthController),
):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing"
        )
    tokens = await auth_controller.refresh(refresh_token)

    # Update the refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/api/v1/auth/refresh-token"
    )

    # Return access token and role
    return Token(
        access_token=tokens.access_token,
        refresh_token="",  # Empty as it's in the cookie
        token_type="bearer",
        role=tokens.role,
    )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/users/me")
@handle_exceptions
async def get_current_user_info(
    current_user=Depends(get_current_user),
):
    id = current_user.get("_id", "")
    email = current_user.get("email", "")
    role = current_user.get("role", "")

    final_response = {"id": id, "email": email, "role": role}

    return JSONResponse(
        content={
            "data": final_response,
            "statuscode": 200,
            "detail": "user info fetched successfully",
            "error": "",
        },
        status_code=status.HTTP_200_OK,
    )
