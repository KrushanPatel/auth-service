from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import services.password_reset_service as password_reset_service
from core.jwt import create_password_reset_token
from core.security import hash_password


async def test_request_password_reset_creates_token_for_known_user(monkeypatch):
    user = {"id": uuid4(), "email": "krushan@example.com"}
    monkeypatch.setattr(password_reset_service, "get_user_by_email", AsyncMock(return_value=user))
    create_record = AsyncMock(return_value=None)
    monkeypatch.setattr(password_reset_service, "create_password_reset_token_record", create_record)

    token = await password_reset_service.request_password_reset("krushan@example.com")

    assert token is not None
    create_record.assert_awaited_once()
    assert create_record.await_args.kwargs["user_id"] == user["id"]


async def test_request_password_reset_silent_for_unknown_email(monkeypatch):
    monkeypatch.setattr(password_reset_service, "get_user_by_email", AsyncMock(return_value=None))
    create_record = AsyncMock(return_value=None)
    monkeypatch.setattr(password_reset_service, "create_password_reset_token_record", create_record)

    token = await password_reset_service.request_password_reset("nobody@example.com")

    assert token is None
    create_record.assert_not_awaited()


async def test_reset_password_success(monkeypatch):
    user_id = uuid4()
    token, jti = create_password_reset_token(str(user_id))
    db_token = {
        "used": False,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
        "token_hash": hash_password(token),
    }
    monkeypatch.setattr(
        password_reset_service, "get_password_reset_token_by_jti", AsyncMock(return_value=db_token)
    )
    mark_used = AsyncMock(return_value=None)
    monkeypatch.setattr(password_reset_service, "mark_password_reset_token_used", mark_used)
    update_user = AsyncMock(return_value=None)
    monkeypatch.setattr(password_reset_service, "update_user", update_user)
    revoke_all = AsyncMock(return_value=None)
    monkeypatch.setattr(password_reset_service, "revoke_all_refresh_token_for_user", revoke_all)

    await password_reset_service.reset_password(token, "NewPassword@123")

    mark_used.assert_awaited_once_with(jti)
    update_user.assert_awaited_once()
    assert update_user.await_args.args[0] == str(user_id)
    revoke_all.assert_awaited_once_with(user_id)


async def test_reset_password_not_found(monkeypatch):
    monkeypatch.setattr(
        password_reset_service, "get_password_reset_token_by_jti", AsyncMock(return_value=None)
    )
    token, _ = create_password_reset_token(str(uuid4()))

    with pytest.raises(HTTPException) as exc_info:
        await password_reset_service.reset_password(token, "NewPassword@123")

    assert exc_info.value.status_code == 400


async def test_reset_password_already_used(monkeypatch):
    token, _ = create_password_reset_token(str(uuid4()))
    db_token = {
        "used": True,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
        "token_hash": hash_password(token),
    }
    monkeypatch.setattr(
        password_reset_service, "get_password_reset_token_by_jti", AsyncMock(return_value=db_token)
    )

    with pytest.raises(HTTPException) as exc_info:
        await password_reset_service.reset_password(token, "NewPassword@123")

    assert exc_info.value.status_code == 400


async def test_reset_password_expired(monkeypatch):
    token, _ = create_password_reset_token(str(uuid4()))
    db_token = {
        "used": False,
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
        "token_hash": hash_password(token),
    }
    monkeypatch.setattr(
        password_reset_service, "get_password_reset_token_by_jti", AsyncMock(return_value=db_token)
    )

    with pytest.raises(HTTPException) as exc_info:
        await password_reset_service.reset_password(token, "NewPassword@123")

    assert exc_info.value.status_code == 400


async def test_reset_password_hash_mismatch(monkeypatch):
    token, _ = create_password_reset_token(str(uuid4()))
    db_token = {
        "used": False,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
        "token_hash": hash_password("a-different-token"),
    }
    monkeypatch.setattr(
        password_reset_service, "get_password_reset_token_by_jti", AsyncMock(return_value=db_token)
    )

    with pytest.raises(HTTPException) as exc_info:
        await password_reset_service.reset_password(token, "NewPassword@123")

    assert exc_info.value.status_code == 400


async def test_cleanup_expired_password_reset_tokens_calls_repo(monkeypatch):
    delete_expired = AsyncMock(return_value=None)
    monkeypatch.setattr(
        password_reset_service, "delete_expired_password_reset_tokens", delete_expired
    )

    await password_reset_service.cleanup_expired_password_reset_tokens()

    delete_expired.assert_awaited_once()
