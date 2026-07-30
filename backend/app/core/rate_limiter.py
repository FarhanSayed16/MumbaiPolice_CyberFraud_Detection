import time
import logging
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from app.core.redis_pool import get_redis_client

logger = logging.getLogger(__name__)

# In-memory sliding window fallback (`ip -> list of timestamps`) if Redis is unavailable
_in_memory_store: Dict[str, list[float]] = {}


async def check_rate_limit(request: Request, max_requests: int = 5, window_seconds: int = 60):
    """
    Sliding window rate limiter protecting critical endpoints (e.g. `/api/v1/auth/login` `Sub-phase 5.1`).
    Backed by Redis if available, with automatic failover to thread-safe in-memory sliding window.
    """
    ip_address = request.client.host if request.client else "127.0.0.1"
    key = f"rate_limit:login:{ip_address}"
    now = time.time()

    redis = get_redis_client()
    if redis:
        try:
            async with redis.pipeline(transaction=True) as pipe:
                # Remove timestamps outside window
                pipe.zremrangebyscore(key, 0, now - window_seconds)
                # Count remaining requests in window
                pipe.zcard(key)
                # Add current request timestamp
                pipe.zadd(key, {str(now): now})
                # Set key TTL
                pipe.expire(key, window_seconds + 5)
                results = await pipe.execute()
                
                request_count = results[1]
                if request_count >= max_requests:
                    logger.warning(f"[SECURITY ALERT] Rate limit exceeded on login for IP: {ip_address} ({request_count}/{max_requests})")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Too many login attempts ({request_count}/{max_requests}). Please wait {window_seconds} seconds.",
                        headers={"Retry-After": str(window_seconds)}
                    )
                return
        except HTTPException:
            raise
        except Exception as e:
            logger.debug(f"Redis rate limit check failed, falling back to in-memory: {e}")

    # In-memory sliding window fallback
    timestamps = _in_memory_store.get(ip_address, [])
    # Filter out expired timestamps
    valid_timestamps = [ts for ts in timestamps if (now - ts) < window_seconds]
    
    if len(valid_timestamps) >= max_requests:
        logger.warning(f"[SECURITY ALERT] In-memory rate limit exceeded on login for IP: {ip_address}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please wait {window_seconds} seconds.",
            headers={"Retry-After": str(window_seconds)}
        )

    valid_timestamps.append(now)
    _in_memory_store[ip_address] = valid_timestamps
