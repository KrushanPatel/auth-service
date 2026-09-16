import secrets
from datetime import datetime, timezone

import pyotp
from fastapi import HTTPException, status

from core.config import MFA_RECOVERY_CODE_COUNT, TOTP_VALID_WINDOW
from core.jwt import create_access_token, create_refresh_token
from core.mfa_crypto import decrypt_secret, encrypt_secret
from core.security import hash_reset_token, verify_password
from repositories.mfa_repository import (
    activate_mfa,
    deactivate_mfa,
    delete_recovery_codes,
    get_recovery_code_by_hash,
    insert_recovery_codes,
    mark_recovery_code_used,
    set_pending_mfa_secret,
)
from repositories.refresh_token_repository import revoke_all_refresh_token_for_user
from repositories.user_repository import get_user_by_id, update_user
from services.refresh_token_service import store_refresh_token


def _generate_recovery_codes() -> list[str]:
    return [secrets.token_urlsafe(8) for _ in range(MFA_RECOVERY_CODE_COUNT)]


async def enroll_mfa(user: dict) -> dict:
    if user["mfa_enabled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled; disable it before re-enrolling",
        )

    secret = pyotp.random_base32()
    otpauth_url = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user["email"], issuer_name="Auth Service"
    )

    await set_pending_mfa_secret(user["id"], encrypt_secret(secret))

    return {"secret": secret, "otpauth_url": otpauth_url}


async def confirm_mfa_enrollment(user: dict, code: str) -> list[str]:
    if user["mfa_enabled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled"
        )

    if not user["mfa_secret"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No MFA enrollment in progress"
        )

    secret = decrypt_secret(user["mfa_secret"])
    if not pyotp.TOTP(secret).verify(code, valid_window=TOTP_VALID_WINDOW):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

    await activate_mfa(user["id"])

    recovery_codes = _generate_recovery_codes()
    await insert_recovery_codes(
        user["id"], [hash_reset_token(raw_code) for raw_code in recovery_codes]
    )

    return recovery_codes


async def disable_mfa(user: dict, password: str) -> None:
    if not user["mfa_enabled"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled")

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    await deactivate_mfa(user["id"])
    await delete_recovery_codes(user["id"])
    await revoke_all_refresh_token_for_user(user["id"])
    await update_user(str(user["id"]), tokens_valid_after=datetime.now(timezone.utc))


async def verify_mfa_login(user_id: str, code: str) -> dict:
    user = await get_user_by_id(user_id)

    if user is None or not user["mfa_enabled"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA token")

    secret = decrypt_secret(user["mfa_secret"])

    if not pyotp.TOTP(secret).verify(code, valid_window=TOTP_VALID_WINDOW):
        recovery_code = await get_recovery_code_by_hash(user["id"], hash_reset_token(code))
        if recovery_code is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")
        await mark_recovery_code_used(recovery_code["id"])

    access_token = create_access_token(str(user["id"]))
    refresh_token, jti = create_refresh_token(str(user["id"]))

    await store_refresh_token(user_id=user["id"], refresh_token=refresh_token, jti=jti)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
