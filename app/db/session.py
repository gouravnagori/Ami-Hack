from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("db.session")

# Handle SQLite vs Postgres connect args
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    connect_args=connect_args,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
async_session_factory = async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


get_db_session = get_db


# Redis connection pool
_redis_pool: aioredis.ConnectionPool | None = None


def get_redis_pool() -> aioredis.ConnectionPool:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def get_redis() -> AsyncGenerator[aioredis.Redis | None, None]:
    """Yields Redis connection with graceful fallback if Redis service is unreachable."""
    client: aioredis.Redis | None = None
    try:
        pool = get_redis_pool()
        client = aioredis.Redis(connection_pool=pool)
        yield client
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))
        yield None
    finally:
        if client is not None:
            await client.aclose()


async def check_db_health() -> bool:
    try:
        from sqlalchemy import text

        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error("db_health_check_failed", error=str(e))
        return False


async def check_redis_health() -> bool:
    try:
        pool = get_redis_pool()
        client = aioredis.Redis(connection_pool=pool)
        await client.ping()
        await client.aclose()
        return True
    except Exception as e:
        logger.warning("redis_health_check_failed", error=str(e))
        return False
