from datetime import datetime, timezone
from uuid import UUID

from core.config import REFRESH_TOKEN_EXPIRE
from core.jwt import verify_refresh_token
from core.security import hash_password, verify_password

from repositories.refresh_token_repository import (
    create_refresh_token_record,
    get_refresh_token_by_jti,
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
        raise ValueError("Refresh token has been revoked")

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