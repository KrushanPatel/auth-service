from datetime import timedelta

from db.redis_connection import get_redis_client
from repositories.rate_limit_repository import increment_rate_limit


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


async def test_increment_rate_limit_sets_a_ttl():
    await increment_rate_limit("1.2.3.4", "login", timedelta(minutes=1))

    ttl = await get_redis_client().ttl("ratelimit:login:1.2.3.4")
    assert 0 < ttl <= 60
