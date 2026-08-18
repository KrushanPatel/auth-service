import asyncio
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from core.config import REFRESH_TOKEN_EXPIRE
from core.jwt import create_access_token, create_refresh_token, verify_refresh_token
from core.security import hash_password, verify_password
from repositories.refresh_token_repository import (
    create_refresh_token_record,
    delete_expired_refresh_tokens,
    get_refresh_token_by_jti,
    revoke_all_refresh_token_for_user,
    revoke_refresh_token_by_jti,
    update_refresh_token_last_used,
)


async def store_refresh_token(
    user_id: UUID,
    refresh_token: str,
    jti: UUID,
):
    """
    Hash and store a refresh token in the database.
    """

    token_hash = hash_password(refresh_token)

    expires_at = datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE

    return await create_refresh_token_record(
        user_id=user_id,
        token_hash=token_hash,
        jti=jti,
        expires_at=expires_at,
    )


async def validate_refresh_token(
    refresh_token: str,
) -> UUID:
    """
    Validate a refresh token and return the authenticated user's ID.
    """

    payload = verify_refresh_token(refresh_token)

    jti = UUID(payload["jti"])

    db_token = await get_refresh_token_by_jti(jti)

    if db_token is None:
        raise ValueError("Refresh token not found")

    if db_token["revoked"]:
        await revoke_all_refresh_token_for_user(UUID(payload["sub"]))
        raise ValueError("Refresh token reuse detected")
    if db_token["expires_at"] < datetime.now(timezone.utc):
        raise ValueError("Refresh token has expired")

    if not verify_password(
        refresh_token,
        db_token["token_hash"],
    ):
        raise ValueError("Invalid refresh token")

    await update_refresh_token_last_used(jti)

    return UUID(payload["sub"])


async def revoke_refresh_token(
    refresh_token: str,
):
    """
    Revoke a refresh token.
    """

    payload = verify_refresh_token(refresh_token)

    jti = UUID(payload["jti"])

    return await revoke_refresh_token_by_jti(jti)


async def refresh_access_token(
    refresh_token: str,
):
    try:
        user_id = await validate_refresh_token(refresh_token)
    except ValueError as exec:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exec))

    new_token, new_jti = create_refresh_token(str(user_id))
    await store_refresh_token(user_id, new_token, new_jti)
    await revoke_refresh_token(refresh_token)

    access_token = create_access_token(str(user_id))

    return {
        "access_token": access_token,
        "refresh_token": new_token,
        "token_type": "bearer",
    }


async def cleanup_expired_refresh_tokens():
    return await delete_expired_refresh_tokens()


async def cleanup_task():
    while True:
        try:
            await asyncio.sleep(3600)
            await cleanup_expired_refresh_tokens()
            print("Expired refresh token cleaned")

        except asyncio.CancelledError:
            break

        except Exception as exec:
            print(f"Cleanup Failed:{exec}")
