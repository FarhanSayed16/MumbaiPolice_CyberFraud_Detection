import logging
from typing import Optional
from arq import create_pool
from arq.connections import RedisSettings
from redis.asyncio import Redis
from app.config import settings

logger = logging.getLogger(__name__)

# Global ARQ Redis pool instance
arq_pool = None


def get_redis_settings() -> RedisSettings:
    """
    Extracts ARQ RedisSettings from application configuration.
    """
    return RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD or None,
        database=settings.REDIS_DB
    )


async def init_redis_pool():
    """
    Initialize global ARQ Redis pool on startup.
    """
    global arq_pool
    try:
        arq_pool = await create_pool(get_redis_settings())
        logger.info(f"Initialized ARQ Redis Pool connected to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    except Exception as e:
        logger.error(f"Failed to initialize ARQ Redis Pool: {e}")


async def close_redis_pool():
    """
    Close ARQ Redis pool on shutdown.
    """
    global arq_pool
    if arq_pool:
        await arq_pool.close()
        arq_pool = None
        logger.info("ARQ Redis Pool closed.")


async def check_redis_health() -> bool:
    """
    Verifies live connectivity to Redis.
    """
    try:
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        pong = await client.ping()
        await client.aclose()
        return pong is True
    except Exception:
        return False


def get_redis_client() -> Optional[Redis]:
    """
    Returns an async Redis client instance if Redis is configured and available.
    """
    try:
        return Redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None

