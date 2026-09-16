from repositories.mfa_repository import (
    activate_mfa,
    deactivate_mfa,
    delete_recovery_codes,
    get_recovery_code_by_hash,
    insert_recovery_codes,
    mark_recovery_code_used,
    set_pending_mfa_secret,
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


async def test_set_pending_mfa_secret_stores_secret_without_enabling():
    user = await _create_test_user()

    updated = await set_pending_mfa_secret(user["id"], "encrypted-secret")

    assert updated["mfa_secret"] == "encrypted-secret"
    assert updated["mfa_enabled"] is False


async def test_activate_mfa_sets_flag():
    user = await _create_test_user()
    await set_pending_mfa_secret(user["id"], "encrypted-secret")

    updated = await activate_mfa(user["id"])

    assert updated["mfa_enabled"] is True


async def test_deactivate_mfa_clears_secret_and_flag():
    user = await _create_test_user()
    await set_pending_mfa_secret(user["id"], "encrypted-secret")
    await activate_mfa(user["id"])

    updated = await deactivate_mfa(user["id"])

    assert updated["mfa_enabled"] is False
    assert updated["mfa_secret"] is None


async def test_insert_and_get_recovery_code_by_hash():
    user = await _create_test_user()

    await insert_recovery_codes(user["id"], ["hash-one", "hash-two"])

    found = await get_recovery_code_by_hash(user["id"], "hash-one")
    missing = await get_recovery_code_by_hash(user["id"], "no-such-hash")

    assert found is not None
    assert found["used"] is False
    assert missing is None


async def test_mark_recovery_code_used_excludes_it_from_lookup():
    user = await _create_test_user()
    await insert_recovery_codes(user["id"], ["hash-one"])
    code = await get_recovery_code_by_hash(user["id"], "hash-one")

    updated = await mark_recovery_code_used(code["id"])

    assert updated["used"] is True
    assert await get_recovery_code_by_hash(user["id"], "hash-one") is None


async def test_delete_recovery_codes_removes_all_for_user():
    user = await _create_test_user()
    await insert_recovery_codes(user["id"], ["hash-one", "hash-two"])

    await delete_recovery_codes(user["id"])

    assert await get_recovery_code_by_hash(user["id"], "hash-one") is None
    assert await get_recovery_code_by_hash(user["id"], "hash-two") is None
