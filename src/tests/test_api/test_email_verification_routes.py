from helpers import login_user, register_and_login, register_user, verify_user_email

from services.email_verification_service import request_email_verification


async def test_verify_email_activates_account_and_allows_login(client):
    await register_user(client)

    blocked_login = await login_user(client)
    assert blocked_login.status_code == 403

    verify_response = await verify_user_email(client)
    assert verify_response.status_code == 204

    allowed_login = await login_user(client)
    assert allowed_login.status_code == 200


async def test_verify_email_rejects_invalid_token(client):
    response = await client.post("/api/v1/auth/verify-email", json={"token": "not-a-real-token"})

    assert response.status_code == 400


async def test_verify_email_rejects_reused_token(client):
    await register_user(client)
    token = await request_email_verification("krushan@example.com")

    await client.post("/api/v1/auth/verify-email", json={"token": token})
    reuse_response = await client.post("/api/v1/auth/verify-email", json={"token": token})

    assert reuse_response.status_code == 400


async def test_resend_verification_always_returns_generic_message(client):
    await register_user(client)

    registered = await client.post(
        "/api/v1/auth/resend-verification", json={"email": "krushan@example.com"}
    )
    unknown = await client.post(
        "/api/v1/auth/resend-verification", json={"email": "nobody@example.com"}
    )

    assert registered.status_code == 200
    assert unknown.status_code == 200
    assert registered.json() == unknown.json()


async def test_resend_verification_issues_a_working_token(client):
    await register_user(client)

    token = await request_email_verification("krushan@example.com")
    verify_response = await client.post("/api/v1/auth/verify-email", json={"token": token})

    assert verify_response.status_code == 204

    login_response = await login_user(client)
    assert login_response.status_code == 200


async def test_already_verified_user_unaffected_by_resend(client):
    await register_and_login(client)

    await client.post("/api/v1/auth/resend-verification", json={"email": "krushan@example.com"})

    login_response = await login_user(client)
    assert login_response.status_code == 200
