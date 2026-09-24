from datetime import timedelta

from db.redis_connection import get_redis_client


async def increment_rate_limit(key: str, action: str, window: timedelta) -> int:
    """
    Atomically increment the fixed-window counter for (key, action) in Redis.
    The TTL is (re)applied with NX after every increment rather than only
    when the count is 1: if the process died between an INCR and a
    conditional EXPIRE, a count-1-gated TTL would never get set, leaving the
    key stuck at a permanent limit. EXPIRE ... NX is idempotent and immune to
    that, at the cost of one extra call per request.
    """

    client = get_redis_client()
    redis_key = f"ratelimit:{action}:{key}"

    count = await client.incr(redis_key)
    await client.expire(redis_key, int(window.total_seconds()), nx=True)

    return count
