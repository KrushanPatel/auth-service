from datetime import timedelta
from uuid import UUID

import jwt as pyjwt
import pytest

from core import jwt as core_jwt
from core.config import JWT_ALGORITHM, JWT_SECRET_KEY

USER_ID = "11111111-1111-1111-1111-111111111111"


def test_create_and_verify_access_token():
    token = core_jwt.create_access_token(USER_ID)

    payload = core_jwt.verify_access_token(token)

    assert payload["sub"] == USER_ID
    assert payload["type"] == "access"


def test_verify_access_token_rejects_refresh_token():
    refresh_token, _ = core_jwt.create_refresh_token(USER_ID)

    with pytest.raises(ValueError, match="Invalid access token"):
        core_jwt.verify_access_token(refresh_token)


def test_verify_access_token_rejects_garbage_token():
    with pytest.raises(ValueError, match="Invalid token"):
        core_jwt.verify_access_token("not-a-jwt")


def test_verify_access_token_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(core_jwt, "ACCESS_TOKEN_EXPIRE", timedelta(seconds=-1))

    token = core_jwt.create_access_token(USER_ID)

    with pytest.raises(ValueError, match="Token has expired"):
        core_jwt.verify_access_token(token)


def test_verify_access_token_rejects_wrong_signature():
    token = pyjwt.encode(
        {"sub": USER_ID, "type": "access"},
        "a-different-secret",
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(ValueError, match="Invalid token"):
        core_jwt.verify_access_token(token)


def test_create_refresh_token_returns_token_and_jti():
    token, jti = core_jwt.create_refresh_token(USER_ID)

    assert isinstance(jti, UUID)

    payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert payload["jti"] == str(jti)


def test_verify_refresh_token_returns_payload():
    token, jti = core_jwt.create_refresh_token(USER_ID)

    payload = core_jwt.verify_refresh_token(token)

    assert payload["sub"] == USER_ID
    assert payload["jti"] == str(jti)
    assert payload["type"] == "refresh"


def test_verify_refresh_token_rejects_access_token():
    access_token = core_jwt.create_access_token(USER_ID)

    with pytest.raises(ValueError, match="Invalid refresh token"):
        core_jwt.verify_refresh_token(access_token)


def test_verify_refresh_token_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(core_jwt, "REFRESH_TOKEN_EXPIRE", timedelta(seconds=-1))

    token, _ = core_jwt.create_refresh_token(USER_ID)

    with pytest.raises(ValueError, match="Token has expired"):
        core_jwt.verify_refresh_token(token)


def test_create_password_reset_token_returns_token_and_jti():
    token, jti = core_jwt.create_password_reset_token(USER_ID)

    assert isinstance(jti, UUID)

    payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert payload["jti"] == str(jti)
    assert payload["type"] == "password_reset"


def test_verify_password_reset_token_returns_payload():
    token, jti = core_jwt.create_password_reset_token(USER_ID)

    payload = core_jwt.verify_password_reset_token(token)

    assert payload["sub"] == USER_ID
    assert payload["jti"] == str(jti)


def test_verify_password_reset_token_rejects_refresh_token():
    refresh_token, _ = core_jwt.create_refresh_token(USER_ID)

    with pytest.raises(ValueError, match="Invalid password reset token"):
        core_jwt.verify_password_reset_token(refresh_token)


def test_verify_password_reset_token_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(core_jwt, "PASSWORD_RESET_TOKEN_EXPIRE", timedelta(seconds=-1))

    token, _ = core_jwt.create_password_reset_token(USER_ID)

    with pytest.raises(ValueError, match="Token has expired"):
        core_jwt.verify_password_reset_token(token)
