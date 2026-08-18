from helpers import register_and_login, register_user

from services.password_reset_service import request_password_reset


async def test_forgot_password_always_returns_generic_message(client):
    await register_user(client)

    registered = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "krushan@example.com"}
    )
    unknown = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "nobody@example.com"}
    )

    assert registered.status_code == 200
    assert unknown.status_code == 200
    assert registered.json() == unknown.json()


async def test_reset_password_changes_password_and_revokes_sessions(client):
    tokens = await register_and_login(client)

    reset_token = await request_password_reset("krushan@example.com")

    reset_response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "NewPassword@123"},
    )
    assert reset_response.status_code == 204

    old_password_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "krushan@example.com", "password": "Password@123"},
    )
    assert old_password_login.status_code == 401

    new_password_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "krushan@example.com", "password": "NewPassword@123"},
    )
    assert new_password_login.status_code == 200

    stale_refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert stale_refresh.status_code == 400


async def test_reset_password_rejects_reused_token(client):
    await register_and_login(client)
    reset_token = await request_password_reset("krushan@example.com")

    await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "NewPassword@123"},
    )
    reuse_response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "AnotherPassword@123"},
    )

    assert reuse_response.status_code == 400


async def test_reset_password_rejects_invalid_token(client):
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": "NewPassword@123"},
    )

    assert response.status_code == 400
