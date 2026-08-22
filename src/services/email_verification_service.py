import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from core.config import EMAIL_VERIFICATION_TOKEN_EXPIRE
from core.email import schedule_verification_email
from core.security import hash_reset_token
from repositories.email_verification_repository import (
    create_email_verification_token_record,
    delete_expired_email_verification_tokens,
    get_email_verification_token_by_hash,
    mark_email_verification_token_used,
)
from repositories.user_repository import get_user_by_email, update_user


async def issue_email_verification(user_id: UUID, email: str) -> str:
    """
    Generate, store, and schedule delivery of a fresh email verification
    token. Returns the raw token; callers (registration, resend) decide
    whether to expose it (never over the API).
    """

    token = secrets.token_urlsafe(32)
    token_hash = hash_reset_token(token)
    expires_at = datetime.now(timezone.utc) + EMAIL_VERIFICATION_TOKEN_EXPIRE

    await create_email_verification_token_record(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    schedule_verification_email(email, token)

    return token


async def request_email_verification(email: str) -> str | None:
    """
    Re-send a verification email for the given address, if it belongs to a
    registered, not-yet-verified user. Always returns None otherwise, so the
    API layer can respond identically either way (no user enumeration).
    """

    user = await get_user_by_email(email)

    if not user or user["is_verified"]:
        return None

    return await issue_email_verification(user["id"], email)


async def verify_email(token: str) -> None:
    db_token = await get_email_verification_token_by_hash(hash_reset_token(token))

    if db_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email verification token"
        )

    if db_token["used"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification token has already been used",
        )

    if db_token["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email verification token has expired"
        )

    await update_user(str(db_token["user_id"]), is_verified=True)
    await mark_email_verification_token_used(db_token["id"])


async def cleanup_expired_email_verification_tokens():
    return await delete_expired_email_verification_tokens()
