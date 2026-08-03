from fastapi import HTTPException, status

from core.security import hash_password
from repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    update_user
)
from schemas.auth import RegisterRequest, LoginRequest
from core.security import verify_password
from core.jwt import create_access_token


async def register_user(request: RegisterRequest):

    if await get_user_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    if await get_user_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user = await create_user(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
    )

    return {
        **dict(user),
        "message": "User registered successfully",
    }
    
async def login_user(request: LoginRequest):

    user = await get_user_by_email(request.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    if not verify_password(
        request.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = create_access_token(str(user["id"]))
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

async def update_user_service(user_id: str, data):
    update_data = data.model_dump(exclude_none=True)

    return await update_user(user_id, **update_data)