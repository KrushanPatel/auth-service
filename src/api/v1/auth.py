from fastapi import APIRouter
from schemas.auth import RegisterRequest, LoginRequest
from schemas.auth import RegisterResponse, LoginResponse
from services.auth_service import register_user, login_user
router = APIRouter()

@router.post("/register",response_model=RegisterResponse)
async def register(request: RegisterRequest):
    return await register_user(request)

@router.post("/login",response_model=LoginResponse)
async def login(request : LoginRequest):
    return await login_user(request)