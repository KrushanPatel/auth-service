from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import core.dependencies as dependencies
from core.jwt import create_access_token

USER_ID = str(uuid4())


def make_user(**overrides):
    user = {
        "id": USER_ID,
        "username": "krushan",
        "email": "krushan@example.com",
        "is_active": True,
        "tokens_valid_after": None,
    }
    user.update(overrides)
    return user


def credentials(token):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


async def test_get_current_user_accepts_token_issued_after_invalidation(monkeypatch):
    monkeypatch.setattr(
        dependencies,
        "get_user_by_id",
        AsyncMock(
            return_value=make_user(
                tokens_valid_after=datetime.now(timezone.utc) - timedelta(minutes=5)
            )
        ),
    )

    token = create_access_token(USER_ID)

    user = await dependencies.get_current_user(credentials(token))

    assert user["id"] == USER_ID


async def test_get_current_user_rejects_token_issued_before_invalidation(monkeypatch):
    monkeypatch.setattr(
        dependencies,
        "get_user_by_id",
        AsyncMock(
            return_value=make_user(
                tokens_valid_after=datetime.now(timezone.utc) + timedelta(minutes=5)
            )
        ),
    )

    token = create_access_token(USER_ID)

    with pytest.raises(HTTPException) as exc_info:
        await dependencies.get_current_user(credentials(token))

    assert exc_info.value.status_code == 401
