import pyotp
from helpers import login_user, register_and_login


async def _enroll_and_confirm(client, tokens):
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    enroll_response = await client.post("/api/v1/mfa/enroll", headers=headers)
    secret = enroll_response.json()["secret"]

    code = pyotp.TOTP(secret).now()
    confirm_response = await client.post(
        "/api/v1/mfa/enroll/confirm", json={"code": code}, headers=headers
    )

    return secret, confirm_response


async def test_enroll_returns_secret_and_otpauth_url(client):
    tokens = await register_and_login(client)

    response = await client.post(
        "/api/v1/mfa/enroll",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["secret"]
    assert body["otpauth_url"].startswith("otpauth://totp/")


async def test_enroll_confirm_activates_mfa_and_returns_recovery_codes(client):
    tokens = await register_and_login(client)

    _, confirm_response = await _enroll_and_confirm(client, tokens)

    assert confirm_response.status_code == 200
    recovery_codes = confirm_response.json()["recovery_codes"]
    assert len(recovery_codes) == 10


async def test_enroll_confirm_rejects_invalid_code(client):
    tokens = await register_and_login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    await client.post("/api/v1/mfa/enroll", headers=headers)
    response = await client.post(
        "/api/v1/mfa/enroll/confirm", json={"code": "000000"}, headers=headers
    )

    assert response.status_code == 400


async def test_login_requires_mfa_after_enrollment(client):
    tokens = await register_and_login(client)
    secret, confirm_response = await _enroll_and_confirm(client, tokens)
    assert confirm_response.status_code == 200

    login_response = await login_user(client)

    assert login_response.status_code == 200
    body = login_response.json()
    assert body["mfa_required"] is True
    assert "mfa_token" in body


async def test_mfa_verify_completes_login_with_valid_totp_code(client):
    tokens = await register_and_login(client)
    secret, confirm_response = await _enroll_and_confirm(client, tokens)
    assert confirm_response.status_code == 200

    login_response = await login_user(client)
    mfa_token = login_response.json()["mfa_token"]

    verify_response = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": pyotp.TOTP(secret).now()},
    )

    assert verify_response.status_code == 200
    body = verify_response.json()
    assert body["access_token"]
    assert body["refresh_token"]


async def test_mfa_verify_completes_login_with_recovery_code(client):
    tokens = await register_and_login(client)
    secret, confirm_response = await _enroll_and_confirm(client, tokens)
    recovery_code = confirm_response.json()["recovery_codes"][0]

    login_response = await login_user(client)
    mfa_token = login_response.json()["mfa_token"]

    verify_response = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": recovery_code},
    )

    assert verify_response.status_code == 200

    reuse_response = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": recovery_code},
    )
    assert reuse_response.status_code == 401


async def test_mfa_verify_rejects_invalid_code(client):
    tokens = await register_and_login(client)
    secret, confirm_response = await _enroll_and_confirm(client, tokens)
    assert confirm_response.status_code == 200

    login_response = await login_user(client)
    mfa_token = login_response.json()["mfa_token"]

    verify_response = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": "000000"},
    )

    assert verify_response.status_code == 401


async def test_disable_mfa_requires_correct_password_and_stops_challenging_login(client):
    tokens = await register_and_login(client)
    secret, confirm_response = await _enroll_and_confirm(client, tokens)
    assert confirm_response.status_code == 200

    login_response = await login_user(client)
    mfa_token = login_response.json()["mfa_token"]
    current_tokens = (
        await client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": mfa_token, "code": pyotp.TOTP(secret).now()},
        )
    ).json()

    wrong_password = await client.post(
        "/api/v1/mfa/disable",
        json={"password": "wrong-password"},
        headers={"Authorization": f"Bearer {current_tokens['access_token']}"},
    )
    assert wrong_password.status_code == 401

    disable_response = await client.post(
        "/api/v1/mfa/disable",
        json={"password": "Password@123"},
        headers={"Authorization": f"Bearer {current_tokens['access_token']}"},
    )
    assert disable_response.status_code == 204

    login_response_after_disable = await login_user(client)
    assert login_response_after_disable.status_code == 200
    assert "access_token" in login_response_after_disable.json()


async def test_disable_mfa_revokes_existing_sessions(client):
    tokens = await register_and_login(client)
    secret, confirm_response = await _enroll_and_confirm(client, tokens)
    assert confirm_response.status_code == 200

    login_response = await login_user(client)
    mfa_token = login_response.json()["mfa_token"]
    current_tokens = (
        await client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": mfa_token, "code": pyotp.TOTP(secret).now()},
        )
    ).json()

    await client.post(
        "/api/v1/mfa/disable",
        json={"password": "Password@123"},
        headers={"Authorization": f"Bearer {current_tokens['access_token']}"},
    )

    profile_response = await client.get(
        "/api/v1/users/profile",
        headers={"Authorization": f"Bearer {current_tokens['access_token']}"},
    )
    assert profile_response.status_code == 401


async def test_enroll_rejects_when_already_enabled(client):
    tokens = await register_and_login(client)
    secret, confirm_response = await _enroll_and_confirm(client, tokens)
    assert confirm_response.status_code == 200

    login_response = await login_user(client)
    mfa_token = login_response.json()["mfa_token"]
    current_tokens = (
        await client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": mfa_token, "code": pyotp.TOTP(secret).now()},
        )
    ).json()

    re_enroll_response = await client.post(
        "/api/v1/mfa/enroll",
        headers={"Authorization": f"Bearer {current_tokens['access_token']}"},
    )

    assert re_enroll_response.status_code == 400


async def test_mfa_token_cannot_be_used_as_access_token(client):
    tokens = await register_and_login(client)
    secret, confirm_response = await _enroll_and_confirm(client, tokens)
    assert confirm_response.status_code == 200

    login_response = await login_user(client)
    mfa_token = login_response.json()["mfa_token"]

    response = await client.get(
        "/api/v1/users/profile", headers={"Authorization": f"Bearer {mfa_token}"}
    )

    assert response.status_code == 401


async def test_mfa_verify_rate_limited_after_too_many_wrong_codes(client):
    tokens = await register_and_login(client)
    secret, confirm_response = await _enroll_and_confirm(client, tokens)
    assert confirm_response.status_code == 200

    login_response = await login_user(client)
    mfa_token = login_response.json()["mfa_token"]

    for _ in range(5):
        await client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": mfa_token, "code": "000000"},
        )

    response = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": "000000"},
    )

    assert response.status_code == 429
