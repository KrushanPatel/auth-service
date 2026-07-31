from db.connection import get_pool


async def fetch_one(query: str, *args):

    async with get_pool().acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetch_all(query: str, *args):

    async with get_pool().acquire() as conn:
        return await conn.fetch(query, *args)


async def execute(query: str, *args):

    async with get_pool().acquire() as conn:
        return await conn.execute(query, *args)