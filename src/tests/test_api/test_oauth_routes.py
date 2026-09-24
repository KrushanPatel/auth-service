from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

from helpers import register_and_login, register_user, verify_user_email

import services.oauth_service as oauth_service
from core.jwt import create_oauth_state_token, verify_access_token
from core.security import hash_reset_token


def _extract_state(authorize_url: str) -> str:
    query = parse_qs(urlparse(authorize_url).query)
    return query["state"][0]


def _patch_google_calls(monkeypatch, email="krushan@example.com", email_verified=True):
    monkeypatch.setattr(
        oauth_service,
        "exchange_code_for_token",
        AsyncMock(return_value={"access_token": "google-access-token"}),
    )
    monkeypatch.setattr(
        oauth_service,
        "fetch_google_userinfo",
        AsyncMock(
            return_value={
                "sub": "google-sub-123",
                "email": email,
                "email_verified": email_verified,
                "given_name": "Krushan",
                "family_name": "Patel",
            }
        ),
    )


async def test_google_login_returns_authorize_url_and_sets_cookie(client):
    response = await client.get("/api/v1/auth/oauth/google/login")

    assert response.status_code == 200
    assert "authorize_url" in response.json()
    assert "oauth_state_nonce" in response.cookies


async def test_google_callback_creates_new_user_and_returns_tokens(client, monkeypatch):
    _patch_google_calls(monkeypatch, email="new-google-user@example.com")

    login_response = await client.get("/api/v1/auth/oauth/google/login")
    state = _extract_state(login_response.json()["authorize_url"])

    callback_response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "fake-code", "state": state},
    )

    assert callback_response.status_code == 200
    body = callback_response.json()
    assert body["token_type"] == "bearer"

    payload = verify_access_token(body["access_token"])
    assert payload["sub"]


async def test_google_callback_auto_links_existing_account_by_email(client, monkeypatch):
    await register_user(client)
    await verify_user_email(client)
    existing_tokens = await register_and_login(client)
    existing_user_id = verify_access_token(existing_tokens["access_token"])["sub"]

    _patch_google_calls(monkeypatch, email="krushan@example.com")

    login_response = await client.get("/api/v1/auth/oauth/google/login")
    state = _extract_state(login_response.json()["authorize_url"])

    callback_response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "fake-code", "state": state},
    )

    assert callback_response.status_code == 200
    body = callback_response.json()
    assert verify_access_token(body["access_token"])["sub"] == existing_user_id


async def test_google_callback_rejects_unverified_google_email(client, monkeypatch):
    _patch_google_calls(monkeypatch, email_verified=False)

    login_response = await client.get("/api/v1/auth/oauth/google/login")
    state = _extract_state(login_response.json()["authorize_url"])

    callback_response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "fake-code", "state": state},
    )

    assert callback_response.status_code == 403


async def test_google_callback_rejects_missing_state_cookie(client):
    state = create_oauth_state_token(hash_reset_token("some-nonce"))

    callback_response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "fake-code", "state": state},
    )

    assert callback_response.status_code == 401
