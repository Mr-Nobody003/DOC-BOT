import asyncpg

from backend.core.config import get_settings

_pool: asyncpg.Pool | None = None


async def init_postgres_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = await asyncpg.create_pool(
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            host=settings.postgres_host,
            port=settings.postgres_port,
        )
    return _pool


async def get_postgres_pool() -> asyncpg.Pool:
    if _pool is None:
        await init_postgres_pool()
    assert _pool is not None
    return _pool


async def close_postgres_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def check_postgres() -> bool:
    try:
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False
