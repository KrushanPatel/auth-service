from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import services.refresh_token_service as refresh_token_service
from core.jwt import create_refresh_token
from core.security import hash_password, verify_password


async def test_store_refresh_token_hashes_and_persists(monkeypatch):
    create_refresh_token_record = AsyncMock(return_value=None)
    monkeypatch.setattr(
        refresh_token_service, "create_refresh_token_record", create_refresh_token_record
    )

    user_id = uuid4()
    jti = uuid4()
    before = datetime.now(timezone.utc)

    await refresh_token_service.store_refresh_token(
        user_id=user_id, refresh_token="raw-token", jti=jti
    )

    create_refresh_token_record.assert_awaited_once()
    kwargs = create_refresh_token_record.await_args.kwargs
    assert kwargs["user_id"] == user_id
    assert kwargs["jti"] == jti
    assert kwargs["token_hash"] != "raw-token"
    assert verify_password("raw-token", kwargs["token_hash"])
    assert timedelta(days=6, hours=23) < kwargs["expires_at"] - before < timedelta(days=7, hours=1)


async def test_validate_refresh_token_success(monkeypatch):
    user_id = uuid4()
    token, jti = create_refresh_token(str(user_id))
    db_token = {
        "revoked": False,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "token_hash": hash_password(token),
    }
    monkeypatch.setattr(
        refresh_token_service, "get_refresh_token_by_jti", AsyncMock(return_value=db_token)
    )
    update_last_used = AsyncMock(return_value=None)
    monkeypatch.setattr(refresh_token_service, "update_refresh_token_last_used", update_last_used)

    result = await refresh_token_service.validate_refresh_token(token)

    assert result == user_id
    update_last_used.assert_awaited_once_with(jti)


async def test_validate_refresh_token_not_found(monkeypatch):
    monkeypatch.setattr(
        refresh_token_service, "get_refresh_token_by_jti", AsyncMock(return_value=None)
    )
    token, _ = create_refresh_token(str(uuid4()))

    with pytest.raises(ValueError, match="not found"):
        await refresh_token_service.validate_refresh_token(token)


async def test_validate_refresh_token_reuse_detected(monkeypatch):
    user_id = uuid4()
    token, jti = create_refresh_token(str(user_id))
    db_token = {
        "revoked": True,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "token_hash": hash_password(token),
    }
    monkeypatch.setattr(
        refresh_token_service, "get_refresh_token_by_jti", AsyncMock(return_value=db_token)
    )
    revoke_all = AsyncMock(return_value=None)
    monkeypatch.setattr(refresh_token_service, "revoke_all_refresh_token_for_user", revoke_all)

    with pytest.raises(ValueError, match="reuse detected"):
        await refresh_token_service.validate_refresh_token(token)

    revoke_all.assert_awaited_once_with(user_id)


async def test_validate_refresh_token_expired_in_db(monkeypatch):
    token, _ = create_refresh_token(str(uuid4()))
    db_token = {
        "revoked": False,
        "expires_at": datetime.now(timezone.utc) - timedelta(days=1),
        "token_hash": hash_password(token),
    }
    monkeypatch.setattr(
        refresh_token_service, "get_refresh_token_by_jti", AsyncMock(return_value=db_token)
    )

    with pytest.raises(ValueError, match="expired"):
        await refresh_token_service.validate_refresh_token(token)


async def test_validate_refresh_token_hash_mismatch(monkeypatch):
    token, _ = create_refresh_token(str(uuid4()))
    db_token = {
        "revoked": False,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "token_hash": hash_password("a-different-token"),
    }
    monkeypatch.setattr(
        refresh_token_service, "get_refresh_token_by_jti", AsyncMock(return_value=db_token)
    )

    with pytest.raises(ValueError, match="Invalid refresh token"):
        await refresh_token_service.validate_refresh_token(token)


async def test_revoke_refresh_token_calls_repo(monkeypatch):
    revoke_by_jti = AsyncMock(return_value=None)
    monkeypatch.setattr(refresh_token_service, "revoke_refresh_token_by_jti", revoke_by_jti)

    token, jti = create_refresh_token(str(uuid4()))
    await refresh_token_service.revoke_refresh_token(token)

    revoke_by_jti.assert_awaited_once_with(jti)


async def test_refresh_access_token_rotates_and_revokes(monkeypatch):
    user_id = uuid4()
    monkeypatch.setattr(
        refresh_token_service, "validate_refresh_token", AsyncMock(return_value=user_id)
    )
    store_refresh_token = AsyncMock(return_value=None)
    monkeypatch.setattr(refresh_token_service, "store_refresh_token", store_refresh_token)
    revoke_refresh_token = AsyncMock(return_value=None)
    monkeypatch.setattr(refresh_token_service, "revoke_refresh_token", revoke_refresh_token)

    result = await refresh_token_service.refresh_access_token("old-token")

    assert result["token_type"] == "bearer"
    assert result["access_token"]
    assert result["refresh_token"]
    store_refresh_token.assert_awaited_once()
    assert store_refresh_token.await_args.args[0] == user_id
    revoke_refresh_token.assert_awaited_once_with("old-token")


async def test_refresh_access_token_invalid_token(monkeypatch):
    monkeypatch.setattr(
        refresh_token_service,
        "validate_refresh_token",
        AsyncMock(side_effect=ValueError("Refresh token has expired")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await refresh_token_service.refresh_access_token("bad-token")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Refresh token has expired"


async def test_cleanup_expired_refresh_tokens_calls_repo(monkeypatch):
    delete_expired = AsyncMock(return_value=None)
    monkeypatch.setattr(refresh_token_service, "delete_expired_refresh_tokens", delete_expired)

    await refresh_token_service.cleanup_expired_refresh_tokens()

    delete_expired.assert_awaited_once()
