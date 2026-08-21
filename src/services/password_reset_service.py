import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status

from core.config import PASSWORD_RESET_TOKEN_EXPIRE
from core.email import schedule_password_reset_email
from core.security import hash_password, hash_reset_token
from repositories.password_reset_repository import (
    create_password_reset_token_record,
    delete_expired_password_reset_tokens,
    get_password_reset_token_by_hash,
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

    token = secrets.token_urlsafe(32)
    token_hash = hash_reset_token(token)
    expires_at = datetime.now(timezone.utc) + PASSWORD_RESET_TOKEN_EXPIRE

    await create_password_reset_token_record(
        user_id=user["id"],
        token_hash=token_hash,
        expires_at=expires_at,
    )

    schedule_password_reset_email(email, token)

    return token


async def reset_password(token: str, new_password: str) -> None:
    db_token = await get_password_reset_token_by_hash(hash_reset_token(token))

    if db_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password reset token"
        )

    if db_token["used"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has already been used",
        )

    if db_token["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset token has expired"
        )

    await update_user(str(db_token["user_id"]), password_hash=hash_password(new_password))
    await mark_password_reset_token_used(db_token["id"])
    await revoke_all_refresh_token_for_user(db_token["user_id"])


async def cleanup_expired_password_reset_tokens():
    return await delete_expired_password_reset_tokens()
