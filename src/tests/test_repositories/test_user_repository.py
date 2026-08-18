import pytest
from fastapi import HTTPException

from repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    update_user,
)


async def _create_test_user(**overrides):
    data = {
        "username": "krushan",
        "email": "krushan@example.com",
        "password_hash": "hashed-password",
        "first_name": "Krushan",
        "last_name": "Patel",
    }
    data.update(overrides)
    return await create_user(**data)


async def test_create_user_returns_public_fields():
    user = await _create_test_user()

    assert user["username"] == "krushan"
    assert user["email"] == "krushan@example.com"
    assert user["is_verified"] is False
    assert "id" in user


async def test_get_user_by_email_found_and_missing():
    await _create_test_user()

    found = await get_user_by_email("krushan@example.com")
    missing = await get_user_by_email("nobody@example.com")

    assert found is not None
    assert found["username"] == "krushan"
    assert missing is None


async def test_get_user_by_username_found_and_missing():
    await _create_test_user()

    found = await get_user_by_username("krushan")
    missing = await get_user_by_username("nobody")

    assert found is not None
    assert missing is None


async def test_get_user_by_id_found_and_missing():
    created = await _create_test_user()

    found = await get_user_by_id(str(created["id"]))
    missing = await get_user_by_id("00000000-0000-0000-0000-000000000000")

    assert found is not None
    assert found["id"] == created["id"]
    assert missing is None


async def test_update_user_applies_allowed_fields():
    created = await _create_test_user()

    updated = await update_user(str(created["id"]), first_name="Updated")

    assert updated["first_name"] == "Updated"
    assert updated["username"] == "krushan"


async def test_update_user_rejects_disallowed_field():
    created = await _create_test_user()

    with pytest.raises(HTTPException) as exc_info:
        await update_user(str(created["id"]), is_active=False)

    assert exc_info.value.status_code == 401


async def test_update_user_rejects_empty_update():
    created = await _create_test_user()

    with pytest.raises(HTTPException) as exc_info:
        await update_user(str(created["id"]))

    assert exc_info.value.status_code == 422
