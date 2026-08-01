import asyncpg

from core.secrets import get_db_secret

_pool = None

async def create_pool():

    global _pool

    if _pool is None:

        secret = get_db_secret()

        _pool = await asyncpg.create_pool(
            host=secret["host"],
            port=int(secret["port"]),
            user=secret["username"],
            password=secret["password"],
            database=secret["dbname"],
            ssl="require",
            min_size=5,
            max_size=20,
        )


async def close_pool():

    global _pool

    if _pool:
        await _pool.close()


def get_pool():
    return _pool