from datetime import timedelta

from db.session import execute
from repositories.rate_limit_repository import delete_stale_rate_limits, increment_rate_limit


async def test_increment_rate_limit_counts_up_within_window():
    first = await increment_rate_limit("1.2.3.4", "login", timedelta(minutes=1))
    second = await increment_rate_limit("1.2.3.4", "login", timedelta(minutes=1))

    assert first == 1
    assert second == 2


async def test_increment_rate_limit_resets_after_window_expires():
    await increment_rate_limit("1.2.3.4", "login", timedelta(seconds=0))

    count = await increment_rate_limit("1.2.3.4", "login", timedelta(seconds=0))

    assert count == 1


async def test_increment_rate_limit_is_scoped_per_key_and_action():
    await increment_rate_limit("1.2.3.4", "login", timedelta(minutes=1))

    other_key = await increment_rate_limit("5.6.7.8", "login", timedelta(minutes=1))
    other_action = await increment_rate_limit("1.2.3.4", "register", timedelta(minutes=1))

    assert other_key == 1
    assert other_action == 1


async def test_delete_stale_rate_limits_removes_old_rows_only():
    await increment_rate_limit("stale-key", "login", timedelta(minutes=5))
    await increment_rate_limit("fresh-key", "login", timedelta(minutes=5))

    await execute(
        "UPDATE rate_limits SET window_start = now() - interval '2 days' WHERE key = $1",
        "stale-key",
    )

    await delete_stale_rate_limits(timedelta(days=1))

    # The stale row was deleted, so this starts a brand new window at count 1.
    assert await increment_rate_limit("stale-key", "login", timedelta(minutes=5)) == 1
    # The fresh row survived, so this continues its existing window.
    assert await increment_rate_limit("fresh-key", "login", timedelta(minutes=5)) == 2
