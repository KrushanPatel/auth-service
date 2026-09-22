from helpers import register_and_login, register_and_login_as_admin, register_user

from repositories.user_repository import get_user_by_email


async def test_list_users_requires_authorization_header(client):
    response = await client.get("/api/v1/admin/users")

    assert response.status_code == 401


async def test_list_users_rejects_non_admin(client):
    tokens = await register_and_login(client)

    response = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 403


async def test_list_users_returns_users_for_admin(client):
    tokens = await register_and_login_as_admin(client)

    response = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    usernames = {user["username"] for user in response.json()}
    assert "krushan" in usernames


async def test_update_user_role_rejects_non_admin(client):
    tokens = await register_and_login(client)
    target = await get_user_by_email("krushan@example.com")

    response = await client.patch(
        f"/api/v1/admin/users/{target['id']}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 403


async def test_update_user_role_promotes_target_user(client):
    admin_tokens = await register_and_login_as_admin(client, email="admin@example.com")
    await register_user(client, username="target", email="target@example.com")
    target = await get_user_by_email("target@example.com")

    response = await client.patch(
        f"/api/v1/admin/users/{target['id']}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


async def test_update_user_role_missing_user_returns_404(client):
    admin_tokens = await register_and_login_as_admin(client)

    response = await client.patch(
        "/api/v1/admin/users/00000000-0000-0000-0000-000000000000/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )

    assert response.status_code == 404
