from unittest.mock import AsyncMock
from uuid import uuid4

import pyotp
import pytest
from fastapi import HTTPException

import services.mfa_service as mfa_service


def _user(**overrides):
    base = {
        "id": uuid4(),
        "email": "krushan@example.com",
        "password_hash": "hashed-password",
        "mfa_enabled": False,
        "mfa_secret": None,
    }
    base.update(overrides)
    return base


async def test_enroll_mfa_rejects_when_already_enabled():
    user = _user(mfa_enabled=True)

    with pytest.raises(HTTPException) as exc_info:
        await mfa_service.enroll_mfa(user)

    assert exc_info.value.status_code == 400


async def test_enroll_mfa_stores_encrypted_secret_and_returns_otpauth_url(monkeypatch):
    user = _user()
    set_pending = AsyncMock(return_value=None)
    monkeypatch.setattr(mfa_service, "set_pending_mfa_secret", set_pending)

    result = await mfa_service.enroll_mfa(user)

    assert result["secret"]
    assert result["otpauth_url"].startswith("otpauth://totp/")
    set_pending.assert_awaited_once()
    assert set_pending.await_args.args[0] == user["id"]


async def test_confirm_mfa_enrollment_rejects_when_already_enabled():
    user = _user(mfa_enabled=True)

    with pytest.raises(HTTPException) as exc_info:
        await mfa_service.confirm_mfa_enrollment(user, "123456")

    assert exc_info.value.status_code == 400


async def test_confirm_mfa_enrollment_rejects_without_pending_secret():
    user = _user(mfa_secret=None)

    with pytest.raises(HTTPException) as exc_info:
        await mfa_service.confirm_mfa_enrollment(user, "123456")

    assert exc_info.value.status_code == 400


async def test_confirm_mfa_enrollment_rejects_invalid_code(monkeypatch):
    secret = pyotp.random_base32()
    user = _user(mfa_secret="encrypted-secret")
    monkeypatch.setattr(mfa_service, "decrypt_secret", lambda _: secret)

    with pytest.raises(HTTPException) as exc_info:
        await mfa_service.confirm_mfa_enrollment(user, "000000")

    assert exc_info.value.status_code == 400


async def test_confirm_mfa_enrollment_activates_and_returns_recovery_codes(monkeypatch):
    secret = pyotp.random_base32()
    user = _user(mfa_secret="encrypted-secret")
    monkeypatch.setattr(mfa_service, "decrypt_secret", lambda _: secret)
    activate = AsyncMock(return_value=None)
    monkeypatch.setattr(mfa_service, "activate_mfa", activate)
    insert_codes = AsyncMock(return_value=None)
    monkeypatch.setattr(mfa_service, "insert_recovery_codes", insert_codes)

    code = pyotp.TOTP(secret).now()
    recovery_codes = await mfa_service.confirm_mfa_enrollment(user, code)

    assert len(recovery_codes) == 10
    activate.assert_awaited_once_with(user["id"])
    insert_codes.assert_awaited_once()


async def test_disable_mfa_rejects_when_not_enabled():
    user = _user(mfa_enabled=False)

    with pytest.raises(HTTPException) as exc_info:
        await mfa_service.disable_mfa(user, "Password@123")

    assert exc_info.value.status_code == 400


async def test_disable_mfa_rejects_wrong_password(monkeypatch):
    user = _user(mfa_enabled=True)
    monkeypatch.setattr(mfa_service, "verify_password", lambda password, hashed: False)

    with pytest.raises(HTTPException) as exc_info:
        await mfa_service.disable_mfa(user, "wrong-password")

    assert exc_info.value.status_code == 401


async def test_disable_mfa_clears_state_and_revokes_sessions(monkeypatch):
    user = _user(mfa_enabled=True)
    monkeypatch.setattr(mfa_service, "verify_password", lambda password, hashed: True)
    deactivate = AsyncMock(return_value=None)
    monkeypatch.setattr(mfa_service, "deactivate_mfa", deactivate)
    delete_codes = AsyncMock(return_value=None)
    monkeypatch.setattr(mfa_service, "delete_recovery_codes", delete_codes)
    revoke = AsyncMock(return_value=None)
    monkeypatch.setattr(mfa_service, "revoke_all_refresh_token_for_user", revoke)
    update_user = AsyncMock(return_value=None)
    monkeypatch.setattr(mfa_service, "update_user", update_user)

    await mfa_service.disable_mfa(user, "Password@123")

    deactivate.assert_awaited_once_with(user["id"])
    delete_codes.assert_awaited_once_with(user["id"])
    revoke.assert_awaited_once_with(user["id"])


async def test_verify_mfa_login_rejects_when_mfa_not_enabled(monkeypatch):
    user = _user(mfa_enabled=False)
    monkeypatch.setattr(mfa_service, "get_user_by_id", AsyncMock(return_value=user))

    with pytest.raises(HTTPException) as exc_info:
        await mfa_service.verify_mfa_login(str(user["id"]), "123456")

    assert exc_info.value.status_code == 401


async def test_verify_mfa_login_accepts_valid_totp_code(monkeypatch):
    secret = pyotp.random_base32()
    user = _user(mfa_enabled=True, mfa_secret="encrypted-secret")
    monkeypatch.setattr(mfa_service, "get_user_by_id", AsyncMock(return_value=user))
    monkeypatch.setattr(mfa_service, "decrypt_secret", lambda _: secret)
    store_refresh_token = AsyncMock(return_value=None)
    monkeypatch.setattr(mfa_service, "store_refresh_token", store_refresh_token)

    code = pyotp.TOTP(secret).now()
    result = await mfa_service.verify_mfa_login(str(user["id"]), code)

    assert result["token_type"] == "bearer"
    assert result["access_token"]
    assert result["refresh_token"]


async def test_verify_mfa_login_accepts_valid_recovery_code(monkeypatch):
    secret = pyotp.random_base32()
    user = _user(mfa_enabled=True, mfa_secret="encrypted-secret")
    monkeypatch.setattr(mfa_service, "get_user_by_id", AsyncMock(return_value=user))
    monkeypatch.setattr(mfa_service, "decrypt_secret", lambda _: secret)
    monkeypatch.setattr(
        mfa_service, "get_recovery_code_by_hash", AsyncMock(return_value={"id": uuid4()})
    )
    mark_used = AsyncMock(return_value=None)
    monkeypatch.setattr(mfa_service, "mark_recovery_code_used", mark_used)
    monkeypatch.setattr(mfa_service, "store_refresh_token", AsyncMock(return_value=None))

    result = await mfa_service.verify_mfa_login(str(user["id"]), "a-recovery-code")

    assert result["access_token"]
    mark_used.assert_awaited_once()


async def test_verify_mfa_login_rejects_invalid_code(monkeypatch):
    secret = pyotp.random_base32()
    user = _user(mfa_enabled=True, mfa_secret="encrypted-secret")
    monkeypatch.setattr(mfa_service, "get_user_by_id", AsyncMock(return_value=user))
    monkeypatch.setattr(mfa_service, "decrypt_secret", lambda _: secret)
    monkeypatch.setattr(mfa_service, "get_recovery_code_by_hash", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await mfa_service.verify_mfa_login(str(user["id"]), "000000")

    assert exc_info.value.status_code == 401
