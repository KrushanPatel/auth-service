from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import services.oauth_service as oauth_service
from core.jwt import create_oauth_state_token
from core.security import hash_reset_token

USER_ID = uuid4()


def make_user(**overrides):
    user = {
        "id": USER_ID,
        "username": "krushan",
        "email": "krushan@example.com",
        "google_id": "google-sub-123",
        "is_active": True,
        "mfa_enabled": False,
    }
    user.update(overrides)
    return user


def make_userinfo(**overrides):
    userinfo = {
        "sub": "google-sub-123",
        "email": "krushan@example.com",
        "email_verified": True,
        "given_name": "Krushan",
        "family_name": "Patel",
    }
    userinfo.update(overrides)
    return userinfo


def state_and_nonce(nonce: str = "test-nonce"):
    return create_oauth_state_token(hash_reset_token(nonce)), nonce


def patch_google_calls(monkeypatch, userinfo=None):
    monkeypatch.setattr(
        oauth_service,
        "exchange_code_for_token",
        AsyncMock(return_value={"access_token": "google-access-token"}),
    )
    monkeypatch.setattr(
        oauth_service,
        "fetch_google_userinfo",
        AsyncMock(return_value=userinfo or make_userinfo()),
    )


async def test_get_google_authorize_url_returns_url_and_nonce():
    authorize_url, nonce = oauth_service.get_google_authorize_url()

    assert authorize_url.startswith(oauth_service.GOOGLE_AUTHORIZE_URL)
    assert nonce


async def test_handle_google_callback_missing_cookie_rejected():
    state, _ = state_and_nonce()

    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.handle_google_callback("some-code", state, None)

    assert exc_info.value.status_code == 401


async def test_handle_google_callback_invalid_state_rejected():
    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.handle_google_callback("some-code", "not-a-jwt", "test-nonce")

    assert exc_info.value.status_code == 401


async def test_handle_google_callback_mismatched_nonce_rejected():
    state, _ = state_and_nonce("nonce-a")

    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.handle_google_callback("some-code", state, "nonce-b")

    assert exc_info.value.status_code == 401


async def test_handle_google_callback_unverified_email_rejected(monkeypatch):
    state, nonce = state_and_nonce()
    patch_google_calls(monkeypatch, userinfo=make_userinfo(email_verified=False))

    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.handle_google_callback("some-code", state, nonce)

    assert exc_info.value.status_code == 403


async def test_handle_google_callback_existing_google_id_fast_path(monkeypatch):
    state, nonce = state_and_nonce()
    patch_google_calls(monkeypatch)

    monkeypatch.setattr(oauth_service, "get_user_by_google_id", AsyncMock(return_value=make_user()))
    get_user_by_email = AsyncMock()
    monkeypatch.setattr(oauth_service, "get_user_by_email", get_user_by_email)
    create_oauth_user = AsyncMock()
    monkeypatch.setattr(oauth_service, "create_oauth_user", create_oauth_user)
    monkeypatch.setattr(oauth_service, "store_refresh_token", AsyncMock())

    result = await oauth_service.handle_google_callback("some-code", state, nonce)

    assert result["token_type"] == "bearer"
    get_user_by_email.assert_not_awaited()
    create_oauth_user.assert_not_awaited()


async def test_handle_google_callback_auto_links_existing_email(monkeypatch):
    state, nonce = state_and_nonce()
    patch_google_calls(monkeypatch)

    monkeypatch.setattr(oauth_service, "get_user_by_google_id", AsyncMock(return_value=None))
    monkeypatch.setattr(oauth_service, "get_user_by_email", AsyncMock(return_value=make_user()))
    link_google_id = AsyncMock(return_value=make_user())
    monkeypatch.setattr(oauth_service, "link_google_id", link_google_id)
    create_oauth_user = AsyncMock()
    monkeypatch.setattr(oauth_service, "create_oauth_user", create_oauth_user)
    monkeypatch.setattr(oauth_service, "store_refresh_token", AsyncMock())

    result = await oauth_service.handle_google_callback("some-code", state, nonce)

    assert result["token_type"] == "bearer"
    link_google_id.assert_awaited_once_with(str(USER_ID), "google-sub-123")
    create_oauth_user.assert_not_awaited()


async def test_handle_google_callback_creates_new_user(monkeypatch):
    state, nonce = state_and_nonce()
    patch_google_calls(monkeypatch)

    monkeypatch.setattr(oauth_service, "get_user_by_google_id", AsyncMock(return_value=None))
    monkeypatch.setattr(oauth_service, "get_user_by_email", AsyncMock(return_value=None))
    monkeypatch.setattr(oauth_service, "get_user_by_username", AsyncMock(return_value=None))
    create_oauth_user = AsyncMock(return_value=make_user())
    monkeypatch.setattr(oauth_service, "create_oauth_user", create_oauth_user)
    monkeypatch.setattr(oauth_service, "store_refresh_token", AsyncMock())

    result = await oauth_service.handle_google_callback("some-code", state, nonce)

    assert result["token_type"] == "bearer"
    create_oauth_user.assert_awaited_once()
    assert create_oauth_user.await_args.kwargs["google_id"] == "google-sub-123"


async def test_handle_google_callback_disabled_account_rejected(monkeypatch):
    state, nonce = state_and_nonce()
    patch_google_calls(monkeypatch)

    monkeypatch.setattr(
        oauth_service,
        "get_user_by_google_id",
        AsyncMock(return_value=make_user(is_active=False)),
    )

    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.handle_google_callback("some-code", state, nonce)

    assert exc_info.value.status_code == 403


async def test_handle_google_callback_mfa_enabled_returns_mfa_token(monkeypatch):
    state, nonce = state_and_nonce()
    patch_google_calls(monkeypatch)

    monkeypatch.setattr(
        oauth_service,
        "get_user_by_google_id",
        AsyncMock(return_value=make_user(mfa_enabled=True)),
    )
    store_refresh_token = AsyncMock()
    monkeypatch.setattr(oauth_service, "store_refresh_token", store_refresh_token)

    result = await oauth_service.handle_google_callback("some-code", state, nonce)

    assert result == {"mfa_required": True, "mfa_token": result["mfa_token"]}
    store_refresh_token.assert_not_awaited()
