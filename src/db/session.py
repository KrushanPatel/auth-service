from db.connection import get_pool

async def fetch_one(query: str, *args):
    async with get_pool().acquire() as conn:
        record = await conn.fetchrow(query, *args)
        return dict(record) if record else None
    

async def fetch_all(query: str, *args):
    async with get_pool().acquire() as conn:
        records = await conn.fetch(query, *args)
        return [dict(record) for record in records]

async def execute(query: str, *args):

    async with get_pool().acquire() as conn:
        return await conn.execute(query, *args)