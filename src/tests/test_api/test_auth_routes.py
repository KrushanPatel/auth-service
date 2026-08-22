from helpers import login_user, register_and_login, register_user


async def test_register_returns_created_user(client):
    response = await register_user(client)

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "krushan"
    assert body["email"] == "krushan@example.com"
    assert body["is_verified"] is False
    assert body["message"] == "User registered successfully"


async def test_register_duplicate_email_conflicts(client):
    await register_user(client)

    response = await register_user(client, username="someone-else")

    assert response.status_code == 409


async def test_login_success_returns_tokens(client):
    await register_user(client)

    response = await login_user(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_wrong_password_rejected(client):
    await register_user(client)

    response = await login_user(client, password="wrong-password")

    assert response.status_code == 401


async def test_login_unknown_email_rejected(client):
    response = await login_user(client, email="nobody@example.com")

    assert response.status_code == 401


async def test_refresh_rotates_tokens(client):
    tokens = await register_and_login(client)

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 200
    rotated = response.json()
    assert rotated["refresh_token"] != tokens["refresh_token"]


async def test_refresh_reuse_of_rotated_token_is_rejected(client):
    tokens = await register_and_login(client)

    await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    reuse_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert reuse_response.status_code == 400


async def test_logout_revokes_refresh_token(client):
    tokens = await register_and_login(client)

    logout_response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout_response.status_code == 204

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 400


async def test_logout_invalidates_access_token_immediately(client):
    tokens = await register_and_login(client)

    profile_response = await client.get(
        "/api/v1/users/profile",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert profile_response.status_code == 200

    logout_response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout_response.status_code == 204

    profile_after_logout = await client.get(
        "/api/v1/users/profile",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert profile_after_logout.status_code == 401
