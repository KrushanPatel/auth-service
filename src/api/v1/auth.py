from fastapi import APIRouter,status,Response
from schemas.auth import RegisterRequest, LoginRequest
from schemas.auth import (
                          RegisterResponse, 
                          LoginResponse,
                          LogoutRequest
                            )
from schemas.refresh_token import (
                            RefreshTokenRequest,
                            RefreshTokenResponse
                        )
from services.auth_service import register_user, login_user,logout_user
from services.refresh_token_service import      (                            
                            refresh_access_token,
                            )


router = APIRouter()

@router.post("/register",response_model=RegisterResponse)
async def register(request: RegisterRequest):
    return await register_user(request)

@router.post("/login",response_model=LoginResponse)
async def login(request : LoginRequest):
    return await login_user(request)

@router.post("/refresh",response_model=RefreshTokenResponse,)
async def refresh_token(request: RefreshTokenRequest,):
    return await refresh_access_token(
        request.refresh_token
    )

@router.post('/logout',status_code=status.HTTP_204_NO_CONTENT)
async def logout(request:LogoutRequest):

    await logout_user(request.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
