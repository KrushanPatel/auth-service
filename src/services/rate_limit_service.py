from datetime import timedelta

from fastapi import HTTPException, status

from repositories.rate_limit_repository import delete_stale_rate_limits, increment_rate_limit

# (limit, window) per action, keyed by client IP.
IP_LIMITS: dict[str, tuple[int, timedelta]] = {
    "login": (20, timedelta(minutes=1)),
    "register": (10, timedelta(minutes=1)),
    "forgot_password": (10, timedelta(minutes=1)),
}

# (limit, window) per action, keyed by the account identifier (email) the
# request targets. Only actions with an existing/targeted account apply here.
ACCOUNT_LIMITS: dict[str, tuple[int, timedelta]] = {
    "login": (5, timedelta(minutes=15)),
    "forgot_password": (3, timedelta(hours=1)),
}

MAX_RATE_LIMIT_WINDOW = max(
    (window for _, window in [*IP_LIMITS.values(), *ACCOUNT_LIMITS.values()]),
    default=timedelta(),
)


async def _check(key: str, action: str, limit: int, window: timedelta) -> None:
    count = await increment_rate_limit(key, action, window)

    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )


async def enforce_rate_limit(action: str, ip: str, account_key: str | None = None) -> None:
    ip_limit, ip_window = IP_LIMITS[action]
    await _check(ip, f"ip:{action}", ip_limit, ip_window)

    if account_key is not None:
        limit, window = ACCOUNT_LIMITS[action]
        await _check(account_key, f"account:{action}", limit, window)


async def cleanup_expired_rate_limits() -> None:
    await delete_stale_rate_limits(MAX_RATE_LIMIT_WINDOW)
