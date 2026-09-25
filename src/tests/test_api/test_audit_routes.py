from helpers import login_user, register_and_login, register_and_login_as_admin, register_user

from repositories.user_repository import get_user_by_email


def _auth(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _list_events(client, tokens, **params):
    response = await client.get("/api/v1/admin/audit-events", params=params, headers=_auth(tokens))
    assert response.status_code == 200
    return response.json()


async def test_audit_events_requires_authorization_header(client):
    response = await client.get("/api/v1/admin/audit-events")

    assert response.status_code == 401


async def test_audit_events_rejects_non_admin(client):
    tokens = await register_and_login(client)

    response = await client.get("/api/v1/admin/audit-events", headers=_auth(tokens))

    assert response.status_code == 403


async def test_audit_events_rejects_out_of_range_limit(client):
    tokens = await register_and_login_as_admin(client)

    response = await client.get(
        "/api/v1/admin/audit-events", params={"limit": 201}, headers=_auth(tokens)
    )

    assert response.status_code == 422


async def test_login_events_record_client_ip_and_user_agent(client):
    admin_tokens = await register_and_login_as_admin(client)
    admin = await get_user_by_email("krushan@example.com")

    await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "Password@123"},
        headers={"User-Agent": "audit-test-agent"},
    )

    failures = await _list_events(client, admin_tokens, event_type="login_failure")
    assert len(failures) == 1
    assert failures[0]["user_id"] is None
    assert failures[0]["ip"] == "127.0.0.1"
    assert failures[0]["user_agent"] == "audit-test-agent"
    assert failures[0]["metadata"] == {"reason": "unknown_account"}

    successes = await _list_events(client, admin_tokens, event_type="login_success")
    assert [e["user_id"] for e in successes] == [str(admin["id"])]
    assert successes[0]["metadata"] == {"method": "password"}


async def test_failed_login_does_not_store_submitted_credentials(client):
    admin_tokens = await register_and_login_as_admin(client)

    await login_user(client, email="krushan@example.com", password="Wrong@Password1")

    events = await _list_events(client, admin_tokens, event_type="login_failure")
    assert events[0]["metadata"] == {"reason": "invalid_password"}
    assert "Wrong@Password1" not in str(events)


async def test_role_change_is_audited_with_actor(client):
    admin_tokens = await register_and_login_as_admin(client, email="admin@example.com")
    admin = await get_user_by_email("admin@example.com")
    await register_user(client, username="target", email="target@example.com")
    target = await get_user_by_email("target@example.com")

    await client.patch(
        f"/api/v1/admin/users/{target['id']}/role",
        json={"role": "admin"},
        headers=_auth(admin_tokens),
    )

    events = await _list_events(client, admin_tokens, user_id=str(target["id"]))
    assert len(events) == 1
    assert events[0]["event_type"] == "role_changed"
    assert events[0]["metadata"] == {
        "actor_id": str(admin["id"]),
        "old_role": "user",
        "new_role": "admin",
    }


async def test_logout_and_refresh_reuse_are_audited(client):
    admin_tokens = await register_and_login_as_admin(client, email="admin@example.com")
    tokens = await register_and_login(client, username="victim", email="victim@example.com")
    victim = await get_user_by_email("victim@example.com")

    await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    await client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})

    event_types = [
        e["event_type"] for e in await _list_events(client, admin_tokens, user_id=str(victim["id"]))
    ]
    assert event_types == ["logout", "refresh_token_reuse_detected", "login_success"]
