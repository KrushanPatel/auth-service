from fastapi import APIRouter, Request, Response, status

from schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from schemas.refresh_token import RefreshTokenRequest, RefreshTokenResponse
from services.auth_service import login_user, logout_user, register_user
from services.email_verification_service import request_email_verification, verify_email
from services.password_reset_service import request_password_reset
from services.password_reset_service import reset_password as reset_password_service
from services.rate_limit_service import enforce_rate_limit
from services.refresh_token_service import (
    refresh_access_token,
)

router = APIRouter()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, http_request: Request):
    await enforce_rate_limit("register", _client_ip(http_request))
    return await register_user(request)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request):
    await enforce_rate_limit("login", _client_ip(http_request), account_key=request.email)
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
async def forgot_password(request: ForgotPasswordRequest, http_request: Request):

    await enforce_rate_limit("forgot_password", _client_ip(http_request), account_key=request.email)
    await request_password_reset(request.email)

    return {
        "message": "If that email is registered, a password reset link has been sent.",
    }


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(request: ResetPasswordRequest):

    await reset_password_service(request.token, request.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email_route(request: VerifyEmailRequest):

    await verify_email(request.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(request: ResendVerificationRequest, http_request: Request):

    await enforce_rate_limit(
        "resend_verification", _client_ip(http_request), account_key=request.email
    )
    await request_email_verification(request.email)

    return {
        "message": "If that email is registered and unverified, a verification link has been sent.",
    }
