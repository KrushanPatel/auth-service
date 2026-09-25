from datetime import datetime, timezone

from fastapi import HTTPException, status

from core.jwt import create_access_token, create_mfa_token, create_refresh_token
from core.security import hash_password, verify_password
from repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    list_users,
    update_user,
    update_user_role,
)
from schemas.auth import LoginRequest, RegisterRequest
from services.audit_service import record_event
from services.email_verification_service import issue_email_verification
from services.refresh_token_service import revoke_refresh_token, store_refresh_token


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

    await issue_email_verification(user["id"], request.email)

    return {
        **dict(user),
        "message": "User registered successfully",
    }


async def login_user(request: LoginRequest):

    user = await get_user_by_email(request.email)

    if not user:
        await record_event("login_failure", reason="unknown_account")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        request.password,
        user["password_hash"],
    ):
        await record_event("login_failure", user["id"], reason="invalid_password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user["is_active"]:
        await record_event("login_failure", user["id"], reason="account_disabled")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    if not user["is_verified"]:
        await record_event("login_failure", user["id"], reason="email_unverified")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    if user["mfa_enabled"]:
        return {
            "mfa_required": True,
            "mfa_token": create_mfa_token(str(user["id"])),
        }

    access_token = create_access_token(str(user["id"]))

    refresh_token, jti = create_refresh_token(str(user["id"]))

    await store_refresh_token(
        user_id=user["id"],
        refresh_token=refresh_token,
        jti=jti,
    )

    await record_event("login_success", user["id"], method="password")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def update_user_service(user_id: str, data):

    update_data = data.model_dump(exclude_none=True)

    return await update_user(user_id, **update_data)


async def list_users_service():
    return await list_users()


async def update_user_role_service(user_id: str, role: str, actor_id):

    existing_user = await get_user_by_id(user_id)

    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_user = await update_user_role(user_id, role)

    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await record_event(
        "role_changed",
        user_id,
        actor_id=str(actor_id),
        old_role=existing_user["role"],
        new_role=role,
    )

    return updated_user


async def logout_user(refresh_token: str):

    try:
        revoked = await revoke_refresh_token(refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token")

    if revoked:
        await update_user(
            str(revoked["user_id"]),
            tokens_valid_after=datetime.now(timezone.utc),
        )
        await record_event("logout", revoked["user_id"])
