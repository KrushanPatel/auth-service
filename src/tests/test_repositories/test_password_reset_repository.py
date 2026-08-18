from datetime import datetime, timedelta, timezone
from uuid import uuid4

from repositories.password_reset_repository import (
    create_password_reset_token_record,
    delete_expired_password_reset_tokens,
    get_password_reset_token_by_jti,
    mark_password_reset_token_used,
)
from repositories.user_repository import create_user


async def _create_test_user():
    return await create_user(
        username="krushan",
        email="krushan@example.com",
        password_hash="hashed-password",
        first_name="Krushan",
        last_name="Patel",
    )


async def _create_token_record(user_id, **overrides):
    data = {
        "user_id": user_id,
        "token_hash": "hashed-reset-token",
        "jti": uuid4(),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    data.update(overrides)
    return await create_password_reset_token_record(**data)


async def test_create_password_reset_token_record_defaults():
    user = await _create_test_user()

    record = await _create_token_record(user["id"])

    assert record["user_id"] == user["id"]
    assert record["used"] is False


async def test_get_password_reset_token_by_jti_found_and_missing():
    user = await _create_test_user()
    created = await _create_token_record(user["id"])

    found = await get_password_reset_token_by_jti(created["jti"])
    missing = await get_password_reset_token_by_jti(uuid4())

    assert found is not None
    assert found["jti"] == created["jti"]
    assert missing is None


async def test_mark_password_reset_token_used_sets_flag():
    user = await _create_test_user()
    created = await _create_token_record(user["id"])

    updated = await mark_password_reset_token_used(created["jti"])

    assert updated["used"] is True


async def test_delete_expired_password_reset_tokens_removes_only_expired():
    user = await _create_test_user()
    expired = await _create_token_record(
        user["id"], expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)
    )
    valid = await _create_token_record(
        user["id"], expires_at=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    await delete_expired_password_reset_tokens()

    assert await get_password_reset_token_by_jti(expired["jti"]) is None
    assert await get_password_reset_token_by_jti(valid["jti"]) is not None
