from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

import services.rate_limit_service as rate_limit_service


async def test_enforce_rate_limit_allows_under_limit(monkeypatch):
    monkeypatch.setattr(rate_limit_service, "IP_LIMITS", {"login": (5, timedelta(minutes=1))})
    monkeypatch.setattr(rate_limit_service, "ACCOUNT_LIMITS", {"login": (5, timedelta(minutes=1))})
    monkeypatch.setattr(rate_limit_service, "increment_rate_limit", AsyncMock(return_value=1))

    await rate_limit_service.enforce_rate_limit("login", "127.0.0.1", account_key="a@example.com")


async def test_enforce_rate_limit_rejects_over_ip_limit(monkeypatch):
    monkeypatch.setattr(rate_limit_service, "IP_LIMITS", {"login": (5, timedelta(minutes=1))})
    monkeypatch.setattr(rate_limit_service, "increment_rate_limit", AsyncMock(return_value=6))

    with pytest.raises(HTTPException) as exc_info:
        await rate_limit_service.enforce_rate_limit("login", "127.0.0.1")

    assert exc_info.value.status_code == 429


async def test_enforce_rate_limit_rejects_over_account_limit(monkeypatch):
    monkeypatch.setattr(rate_limit_service, "IP_LIMITS", {"login": (100, timedelta(minutes=1))})
    monkeypatch.setattr(rate_limit_service, "ACCOUNT_LIMITS", {"login": (5, timedelta(minutes=1))})

    increment = AsyncMock(side_effect=[1, 6])
    monkeypatch.setattr(rate_limit_service, "increment_rate_limit", increment)

    with pytest.raises(HTTPException) as exc_info:
        await rate_limit_service.enforce_rate_limit(
            "login", "127.0.0.1", account_key="a@example.com"
        )

    assert exc_info.value.status_code == 429
    assert increment.await_count == 2


async def test_enforce_rate_limit_skips_account_check_when_no_account_key(monkeypatch):
    monkeypatch.setattr(rate_limit_service, "IP_LIMITS", {"register": (5, timedelta(minutes=1))})
    increment = AsyncMock(return_value=1)
    monkeypatch.setattr(rate_limit_service, "increment_rate_limit", increment)

    await rate_limit_service.enforce_rate_limit("register", "127.0.0.1")

    increment.assert_awaited_once()
