from fastapi import APIRouter
from schemas.auth import RegisterRequest, LoginRequest
from schemas.auth import (
                          RegisterResponse, 
                          LoginResponse,
                          RefreshTokenRequest,
                          RefreshTokenResponse
                            )
from services.auth_service import register_user, login_user,refresh_access_token
router = APIRouter()

@router.post("/register",response_model=RegisterResponse)
async def register(request: RegisterRequest):
    return await register_user(request)

@router.post("/login",response_model=LoginResponse)
async def login(request : LoginRequest):
    return await login_user(request)

@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
)
async def refresh_token(
    request: RefreshTokenRequest,
):
    return await refresh_access_token(
        request.refresh_token
    )
