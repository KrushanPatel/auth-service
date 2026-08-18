from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from core.config import PASSWORD_RESET_TOKEN_EXPIRE
from core.jwt import create_password_reset_token, verify_password_reset_token
from core.security import hash_password, verify_password
from repositories.password_reset_repository import (
    create_password_reset_token_record,
    delete_expired_password_reset_tokens,
    get_password_reset_token_by_jti,
    mark_password_reset_token_used,
)
from repositories.refresh_token_repository import revoke_all_refresh_token_for_user
from repositories.user_repository import get_user_by_email, update_user


async def request_password_reset(email: str) -> str | None:
    """
    Generate and store a password reset token for the given email, if it
    belongs to a registered user. Always returns None to the caller when no
    account exists, so the API layer can respond identically either way and
    avoid leaking whether an email is registered.
    """

    user = await get_user_by_email(email)

    if not user:
        return None

    token, jti = create_password_reset_token(str(user["id"]))

    token_hash = hash_password(token)
    expires_at = datetime.now(timezone.utc) + PASSWORD_RESET_TOKEN_EXPIRE

    await create_password_reset_token_record(
        user_id=user["id"],
        token_hash=token_hash,
        jti=jti,
        expires_at=expires_at,
    )

    print(f"Password reset requested for {email}: token={token}")

    return token


async def reset_password(token: str, new_password: str) -> None:
    try:
        user_id = await _validate_password_reset_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await update_user(str(user_id), password_hash=hash_password(new_password))
    await revoke_all_refresh_token_for_user(user_id)


async def _validate_password_reset_token(token: str) -> UUID:
    payload = verify_password_reset_token(token)

    jti = UUID(payload["jti"])

    db_token = await get_password_reset_token_by_jti(jti)

    if db_token is None:
        raise ValueError("Password reset token not found")

    if db_token["used"]:
        raise ValueError("Password reset token has already been used")

    if db_token["expires_at"] < datetime.now(timezone.utc):
        raise ValueError("Password reset token has expired")

    if not verify_password(token, db_token["token_hash"]):
        raise ValueError("Invalid password reset token")

    await mark_password_reset_token_used(jti)

    return UUID(payload["sub"])


async def cleanup_expired_password_reset_tokens():
    return await delete_expired_password_reset_tokens()
