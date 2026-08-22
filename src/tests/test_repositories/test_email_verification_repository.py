from datetime import datetime, timedelta, timezone

from repositories.email_verification_repository import (
    create_email_verification_token_record,
    delete_expired_email_verification_tokens,
    get_email_verification_token_by_hash,
    mark_email_verification_token_used,
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
        "token_hash": "hashed-verification-token",
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    data.update(overrides)
    return await create_email_verification_token_record(**data)


async def test_create_email_verification_token_record_defaults():
    user = await _create_test_user()

    record = await _create_token_record(user["id"])

    assert record["user_id"] == user["id"]
    assert record["used"] is False


async def test_get_email_verification_token_by_hash_found_and_missing():
    user = await _create_test_user()
    created = await _create_token_record(user["id"])

    found = await get_email_verification_token_by_hash(created["token_hash"])
    missing = await get_email_verification_token_by_hash("no-such-hash")

    assert found is not None
    assert found["id"] == created["id"]
    assert missing is None


async def test_mark_email_verification_token_used_sets_flag():
    user = await _create_test_user()
    created = await _create_token_record(user["id"])

    updated = await mark_email_verification_token_used(created["id"])

    assert updated["used"] is True


async def test_delete_expired_email_verification_tokens_removes_only_expired():
    user = await _create_test_user()
    expired = await _create_token_record(
        user["id"],
        token_hash="expired-hash",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    valid = await _create_token_record(
        user["id"],
        token_hash="valid-hash",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
    )

    await delete_expired_email_verification_tokens()

    assert await get_email_verification_token_by_hash(expired["token_hash"]) is None
    assert await get_email_verification_token_by_hash(valid["token_hash"]) is not None
