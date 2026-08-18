from helpers import register_and_login


async def test_profile_requires_authorization_header(client):
    response = await client.get("/api/v1/users/profile")

    assert response.status_code == 401


async def test_profile_rejects_invalid_token(client):
    response = await client.get(
        "/api/v1/users/profile", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


async def test_profile_returns_current_user(client):
    tokens = await register_and_login(client)

    response = await client.get(
        "/api/v1/users/profile",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "krushan"
    assert body["email"] == "krushan@example.com"


async def test_update_profile_persists_change(client):
    tokens = await register_and_login(client)

    response = await client.patch(
        "/api/v1/users",
        json={"first_name": "Updated"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"
