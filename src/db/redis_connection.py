import redis.asyncio as redis

from core.config import ENV, REDIS_URL

_redis_client = None


def validate_redis_config() -> None:
    """
    Fail fast at startup rather than silently running production against the
    localhost default, which won't exist in an ECS container.
    """
    if ENV == "production" and not REDIS_URL:
        raise RuntimeError("REDIS_URL is not set; cannot rate limit in production")


async def create_redis_client():

    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL)


async def close_redis_client():

    global _redis_client

    if _redis_client:
        await _redis_client.aclose()


def get_redis_client():
    return _redis_client
