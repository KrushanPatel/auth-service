from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import services.auth_service as auth_service
from core.security import hash_password
from schemas.auth import LoginRequest, RegisterRequest
from schemas.user import UserUpdate

USER_ID = uuid4()


def make_user(**overrides):
    user = {
        "id": USER_ID,
        "username": "krushan",
        "email": "krushan@example.com",
        "password_hash": hash_password("Password@123"),
        "first_name": "Krushan",
        "last_name": "Patel",
        "is_verified": True,
        "is_active": True,
        "mfa_enabled": False,
    }
    user.update(overrides)
    return user


def register_request(**overrides):
    data = {
        "username": "krushan",
        "email": "krushan@example.com",
        "password": "Password@123",
        "first_name": "Krushan",
        "last_name": "Patel",
    }
    data.update(overrides)
    return RegisterRequest(**data)


async def test_register_user_success(monkeypatch):
    monkeypatch.setattr(auth_service, "get_user_by_email", AsyncMock(return_value=None))
    monkeypatch.setattr(auth_service, "get_user_by_username", AsyncMock(return_value=None))
    monkeypatch.setattr(
        auth_service,
        "create_user",
        AsyncMock(
            return_value={
                "id": USER_ID,
                "username": "krushan",
                "email": "krushan@example.com",
                "is_verified": False,
            }
        ),
    )
    issue_email_verification = AsyncMock(return_value="some-token")
    monkeypatch.setattr(auth_service, "issue_email_verification", issue_email_verification)

    result = await auth_service.register_user(register_request())

    assert result["id"] == USER_ID
    assert result["message"] == "User registered successfully"
    issue_email_verification.assert_awaited_once_with(USER_ID, "krushan@example.com")


async def test_register_user_duplicate_email(monkeypatch):
    monkeypatch.setattr(auth_service, "get_user_by_email", AsyncMock(return_value=make_user()))
    monkeypatch.setattr(auth_service, "get_user_by_username", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register_user(register_request())

    assert exc_info.value.status_code == 409


async def test_register_user_duplicate_username(monkeypatch):
    monkeypatch.setattr(auth_service, "get_user_by_email", AsyncMock(return_value=None))
    monkeypatch.setattr(auth_service, "get_user_by_username", AsyncMock(return_value=make_user()))

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register_user(register_request())

    assert exc_info.value.status_code == 409


def only_audit_event(audit_events):
    audit_events.assert_awaited_once()
    return audit_events.await_args.kwargs


async def test_login_user_success(monkeypatch, audit_events):
    monkeypatch.setattr(auth_service, "get_user_by_email", AsyncMock(return_value=make_user()))
    store_refresh_token = AsyncMock(return_value=None)
    monkeypatch.setattr(auth_service, "store_refresh_token", store_refresh_token)

    result = await auth_service.login_user(
        LoginRequest(email="krushan@example.com", password="Password@123")
    )

    assert result["token_type"] == "bearer"
    assert result["access_token"]
    assert result["refresh_token"]
    store_refresh_token.assert_awaited_once()
    assert store_refresh_token.await_args.kwargs["user_id"] == USER_ID
    event = only_audit_event(audit_events)
    assert event["event_type"] == "login_success"
    assert event["user_id"] == USER_ID
    assert event["metadata"] == {"method": "password"}


async def test_login_user_unknown_email(monkeypatch, audit_events):
    monkeypatch.setattr(auth_service, "get_user_by_email", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login_user(
            LoginRequest(email="nobody@example.com", password="Password@123")
        )

    assert exc_info.value.status_code == 401
    event = only_audit_event(audit_events)
    assert event["event_type"] == "login_failure"
    assert event["user_id"] is None
    assert event["metadata"] == {"reason": "unknown_account"}


async def test_login_user_inactive_account(monkeypatch, audit_events):
    monkeypatch.setattr(
        auth_service, "get_user_by_email", AsyncMock(return_value=make_user(is_active=False))
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login_user(
            LoginRequest(email="krushan@example.com", password="Password@123")
        )

    assert exc_info.value.status_code == 403
    assert only_audit_event(audit_events)["metadata"] == {"reason": "account_disabled"}


async def test_login_user_unverified_rejected(monkeypatch, audit_events):
    monkeypatch.setattr(
        auth_service, "get_user_by_email", AsyncMock(return_value=make_user(is_verified=False))
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login_user(
            LoginRequest(email="krushan@example.com", password="Password@123")
        )

    assert exc_info.value.status_code == 403
    assert only_audit_event(audit_events)["metadata"] == {"reason": "email_unverified"}


async def test_login_user_mfa_enabled_returns_mfa_token(monkeypatch, audit_events):
    monkeypatch.setattr(
        auth_service, "get_user_by_email", AsyncMock(return_value=make_user(mfa_enabled=True))
    )
    store_refresh_token = AsyncMock(return_value=None)
    monkeypatch.setattr(auth_service, "store_refresh_token", store_refresh_token)

    result = await auth_service.login_user(
        LoginRequest(email="krushan@example.com", password="Password@123")
    )

    assert result == {"mfa_required": True, "mfa_token": result["mfa_token"]}
    assert result["mfa_token"]
    store_refresh_token.assert_not_awaited()
    audit_events.assert_not_awaited()


async def test_login_user_wrong_password(monkeypatch, audit_events):
    monkeypatch.setattr(auth_service, "get_user_by_email", AsyncMock(return_value=make_user()))

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login_user(
            LoginRequest(email="krushan@example.com", password="wrong-password")
        )

    assert exc_info.value.status_code == 401
    event = only_audit_event(audit_events)
    assert event["user_id"] == USER_ID
    assert event["metadata"] == {"reason": "invalid_password"}


async def test_update_user_service_excludes_none_fields(monkeypatch):
    update_user = AsyncMock(return_value={"id": str(USER_ID), "username": "new-name"})
    monkeypatch.setattr(auth_service, "update_user", update_user)

    result = await auth_service.update_user_service(str(USER_ID), UserUpdate(username="new-name"))

    update_user.assert_awaited_once_with(str(USER_ID), username="new-name")
    assert result["username"] == "new-name"


async def test_list_users_service_returns_repository_result(monkeypatch):
    list_users = AsyncMock(return_value=[{"id": USER_ID, "username": "krushan"}])
    monkeypatch.setattr(auth_service, "list_users", list_users)

    result = await auth_service.list_users_service()

    list_users.assert_awaited_once()
    assert result == [{"id": USER_ID, "username": "krushan"}]


async def test_update_user_role_service_success(monkeypatch, audit_events):
    actor_id = uuid4()
    monkeypatch.setattr(
        auth_service, "get_user_by_id", AsyncMock(return_value=make_user(role="user"))
    )
    update_user_role = AsyncMock(return_value={"id": str(USER_ID), "role": "admin"})
    monkeypatch.setattr(auth_service, "update_user_role", update_user_role)

    result = await auth_service.update_user_role_service(str(USER_ID), "admin", actor_id)

    update_user_role.assert_awaited_once_with(str(USER_ID), "admin")
    assert result["role"] == "admin"
    audit_events.assert_awaited_once()
    event = audit_events.await_args.kwargs
    assert event["event_type"] == "role_changed"
    assert event["user_id"] == USER_ID
    assert event["metadata"] == {
        "actor_id": str(actor_id),
        "old_role": "user",
        "new_role": "admin",
    }


async def test_update_user_role_service_missing_user(monkeypatch, audit_events):
    monkeypatch.setattr(auth_service, "get_user_by_id", AsyncMock(return_value=None))
    update_user_role = AsyncMock()
    monkeypatch.setattr(auth_service, "update_user_role", update_user_role)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.update_user_role_service(str(USER_ID), "admin", uuid4())

    assert exc_info.value.status_code == 404
    update_user_role.assert_not_awaited()
    audit_events.assert_not_awaited()


async def test_logout_user_revokes_token(monkeypatch):
    revoke_refresh_token = AsyncMock(return_value=None)
    monkeypatch.setattr(auth_service, "revoke_refresh_token", revoke_refresh_token)
    update_user = AsyncMock()
    monkeypatch.setattr(auth_service, "update_user", update_user)

    await auth_service.logout_user("some-refresh-token")

    revoke_refresh_token.assert_awaited_once_with("some-refresh-token")
    update_user.assert_not_awaited()


async def test_logout_user_invalidates_access_tokens(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "revoke_refresh_token",
        AsyncMock(return_value={"user_id": USER_ID}),
    )
    update_user = AsyncMock()
    monkeypatch.setattr(auth_service, "update_user", update_user)

    await auth_service.logout_user("some-refresh-token")

    update_user.assert_awaited_once()
    args, kwargs = update_user.await_args
    assert args[0] == str(USER_ID)
    assert "tokens_valid_after" in kwargs


async def test_logout_user_invalid_token(monkeypatch):
    monkeypatch.setattr(
        auth_service, "revoke_refresh_token", AsyncMock(side_effect=ValueError("bad token"))
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.logout_user("some-refresh-token")

    assert exc_info.value.status_code == 400
