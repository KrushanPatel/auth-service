from datetime import datetime, timedelta, timezone
from uuid import uuid4

from repositories.refresh_token_repository import (
    create_refresh_token_record,
    delete_expired_refresh_tokens,
    get_refresh_token_by_jti,
    revoke_all_refresh_token_for_user,
    revoke_refresh_token_by_jti,
    update_refresh_token_last_used,
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
        "token_hash": "hashed-refresh-token",
        "jti": uuid4(),
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
    }
    data.update(overrides)
    return await create_refresh_token_record(**data)


async def test_create_refresh_token_record_defaults():
    user = await _create_test_user()

    record = await _create_token_record(user["id"])

    assert record["user_id"] == user["id"]
    assert record["revoked"] is False
    assert record["last_used_at"] is None


async def test_get_refresh_token_by_jti_found_and_missing():
    user = await _create_test_user()
    created = await _create_token_record(user["id"])

    found = await get_refresh_token_by_jti(created["jti"])
    missing = await get_refresh_token_by_jti(uuid4())

    assert found is not None
    assert found["jti"] == created["jti"]
    assert missing is None


async def test_revoke_refresh_token_by_jti_marks_revoked():
    user = await _create_test_user()
    created = await _create_token_record(user["id"])

    revoked = await revoke_refresh_token_by_jti(created["jti"])

    assert revoked["revoked"] is True


async def test_update_refresh_token_last_used_sets_timestamp():
    user = await _create_test_user()
    created = await _create_token_record(user["id"])
    assert created["last_used_at"] is None

    updated = await update_refresh_token_last_used(created["jti"])

    assert updated["last_used_at"] is not None


async def test_delete_expired_refresh_tokens_removes_only_expired():
    user = await _create_test_user()
    expired = await _create_token_record(
        user["id"], expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    valid = await _create_token_record(
        user["id"], expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )

    await delete_expired_refresh_tokens()

    assert await get_refresh_token_by_jti(expired["jti"]) is None
    assert await get_refresh_token_by_jti(valid["jti"]) is not None


async def test_revoke_all_refresh_token_for_user_only_affects_active_tokens():
    user = await _create_test_user()
    active_one = await _create_token_record(user["id"])
    active_two = await _create_token_record(user["id"])
    already_revoked = await _create_token_record(user["id"])
    await revoke_refresh_token_by_jti(already_revoked["jti"])

    revoked = await revoke_all_refresh_token_for_user(user["id"])

    revoked_jtis = {row["jti"] for row in revoked}
    assert revoked_jtis == {active_one["jti"], active_two["jti"]}

    still_revoked_once = await get_refresh_token_by_jti(already_revoked["jti"])
    assert still_revoked_once["revoked"] is True
