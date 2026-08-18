from fastapi import APIRouter, Response, status

from schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
)
from schemas.refresh_token import RefreshTokenRequest, RefreshTokenResponse
from services.auth_service import login_user, logout_user, register_user
from services.password_reset_service import request_password_reset
from services.password_reset_service import reset_password as reset_password_service
from services.refresh_token_service import (
    refresh_access_token,
)

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    return await register_user(request)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    return await login_user(request)


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
)
async def refresh_token(
    request: RefreshTokenRequest,
):
    return await refresh_access_token(request.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: LogoutRequest):

    await logout_user(request.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest):

    await request_password_reset(request.email)

    return {
        "message": "If that email is registered, a password reset link has been sent.",
    }


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(request: ResetPasswordRequest):

    await reset_password_service(request.token, request.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
