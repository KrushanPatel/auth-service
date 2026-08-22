from datetime import timedelta

from db.session import execute, fetch_one


async def increment_rate_limit(key: str, action: str, window: timedelta) -> int:
    """
    Atomically increment the fixed-window counter for (key, action), resetting
    it first if the current window has expired. Returns the count after the
    increment.
    """

    query = """
        INSERT INTO rate_limits (key, action, window_start, count)
        VALUES ($1, $2, now(), 1)
        ON CONFLICT (key, action) DO UPDATE
        SET
            count = CASE
                WHEN rate_limits.window_start <= now() - $3::interval THEN 1
                ELSE rate_limits.count + 1
            END,
            window_start = CASE
                WHEN rate_limits.window_start <= now() - $3::interval THEN now()
                ELSE rate_limits.window_start
            END
        RETURNING count;
    """

    row = await fetch_one(query, key, action, window)
    return row["count"]


async def delete_stale_rate_limits(max_age: timedelta) -> None:
    query = """
        DELETE FROM rate_limits
        WHERE window_start <= now() - $1::interval;
    """

    await execute(query, max_age)
