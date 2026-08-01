from fastapi import APIRouter
from schemas.auth import RegisterRequest, LoginRequest
from services.auth_service import register_user, login_user
router = APIRouter()

@router.post("/register")
async def register(request: RegisterRequest):
    return await register_user(request)

@router.post("/login")
async def login(request : LoginRequest):
    return await login_user(request)