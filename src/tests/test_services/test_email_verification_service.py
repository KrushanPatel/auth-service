from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import services.email_verification_service as email_verification_service
from core.security import hash_reset_token


async def test_issue_email_verification_creates_and_schedules(monkeypatch):
    user_id = uuid4()
    create_record = AsyncMock(return_value=None)
    monkeypatch.setattr(
        email_verification_service, "create_email_verification_token_record", create_record
    )
    schedule_email = MagicMock(return_value=None)
    monkeypatch.setattr(email_verification_service, "schedule_verification_email", schedule_email)

    token = await email_verification_service.issue_email_verification(
        user_id, "krushan@example.com"
    )

    assert token is not None
    create_record.assert_awaited_once()
    kwargs = create_record.await_args.kwargs
    assert kwargs["user_id"] == user_id
    assert kwargs["token_hash"] == hash_reset_token(token)
    schedule_email.assert_called_once_with("krushan@example.com", token)


async def test_request_email_verification_for_unverified_user(monkeypatch):
    user = {"id": uuid4(), "is_verified": False}
    monkeypatch.setattr(
        email_verification_service, "get_user_by_email", AsyncMock(return_value=user)
    )
    monkeypatch.setattr(
        email_verification_service,
        "issue_email_verification",
        AsyncMock(return_value="some-token"),
    )

    token = await email_verification_service.request_email_verification("krushan@example.com")

    assert token == "some-token"


async def test_request_email_verification_silent_for_unknown_email(monkeypatch):
    monkeypatch.setattr(
        email_verification_service, "get_user_by_email", AsyncMock(return_value=None)
    )
    issue = AsyncMock()
    monkeypatch.setattr(email_verification_service, "issue_email_verification", issue)

    token = await email_verification_service.request_email_verification("nobody@example.com")

    assert token is None
    issue.assert_not_awaited()


async def test_request_email_verification_silent_for_already_verified_user(monkeypatch):
    user = {"id": uuid4(), "is_verified": True}
    monkeypatch.setattr(
        email_verification_service, "get_user_by_email", AsyncMock(return_value=user)
    )
    issue = AsyncMock()
    monkeypatch.setattr(email_verification_service, "issue_email_verification", issue)

    token = await email_verification_service.request_email_verification("krushan@example.com")

    assert token is None
    issue.assert_not_awaited()


async def test_verify_email_success(monkeypatch):
    token = "a-raw-verification-token"
    user_id = uuid4()
    db_token = {
        "id": uuid4(),
        "user_id": user_id,
        "used": False,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
        "token_hash": hash_reset_token(token),
    }
    monkeypatch.setattr(
        email_verification_service,
        "get_email_verification_token_by_hash",
        AsyncMock(return_value=db_token),
    )
    mark_used = AsyncMock(return_value=None)
    monkeypatch.setattr(email_verification_service, "mark_email_verification_token_used", mark_used)
    update_user = AsyncMock(return_value=None)
    monkeypatch.setattr(email_verification_service, "update_user", update_user)

    await email_verification_service.verify_email(token)

    update_user.assert_awaited_once_with(str(user_id), is_verified=True)
    mark_used.assert_awaited_once_with(db_token["id"])


async def test_verify_email_not_found(monkeypatch):
    monkeypatch.setattr(
        email_verification_service,
        "get_email_verification_token_by_hash",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        await email_verification_service.verify_email("not-a-real-token")

    assert exc_info.value.status_code == 400


async def test_verify_email_already_used(monkeypatch):
    token = "a-raw-verification-token"
    db_token = {
        "id": uuid4(),
        "user_id": uuid4(),
        "used": True,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
        "token_hash": hash_reset_token(token),
    }
    monkeypatch.setattr(
        email_verification_service,
        "get_email_verification_token_by_hash",
        AsyncMock(return_value=db_token),
    )

    with pytest.raises(HTTPException) as exc_info:
        await email_verification_service.verify_email(token)

    assert exc_info.value.status_code == 400


async def test_verify_email_expired(monkeypatch):
    token = "a-raw-verification-token"
    db_token = {
        "id": uuid4(),
        "user_id": uuid4(),
        "used": False,
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
        "token_hash": hash_reset_token(token),
    }
    monkeypatch.setattr(
        email_verification_service,
        "get_email_verification_token_by_hash",
        AsyncMock(return_value=db_token),
    )

    with pytest.raises(HTTPException) as exc_info:
        await email_verification_service.verify_email(token)

    assert exc_info.value.status_code == 400


async def test_cleanup_expired_email_verification_tokens_calls_repo(monkeypatch):
    delete_expired = AsyncMock(return_value=None)
    monkeypatch.setattr(
        email_verification_service, "delete_expired_email_verification_tokens", delete_expired
    )

    await email_verification_service.cleanup_expired_email_verification_tokens()

    delete_expired.assert_awaited_once()
