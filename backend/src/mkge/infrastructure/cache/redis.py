"""Redis-based rate limiter using sliding window counter."""
import logging
import time

import redis.asyncio as redis

from src.mkge.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def check_rate_limit(
    user_id: str,
    action: str,
    max_count: int,
    window_seconds: int = 3600,
) -> tuple[bool, int]:
    """Check if user has exceeded the rate limit for a given action.

    Returns (allowed, current_count).
    """
    r = _get_redis()
    key = f"rate_limit:{action}:{user_id}"
    now = time.time()
    window_start = now - window_seconds

    pipe = r.pipeline()
    # Remove expired entries
    pipe.zremrangebyscore(key, 0, window_start)
    # Count current entries
    pipe.zcard(key)
    # Add current request
    pipe.zadd(key, {f"{now}": now})
    # Set TTL on key
    pipe.expire(key, window_seconds)

    try:
        results = await pipe.execute()
        current_count = results[1]  # zcard result
    except Exception as e:
        logger.warning("Redis rate limit check failed: %s", e)
        # Fail open: allow the request if Redis is down
        return True, 0

    allowed = current_count < max_count
    if not allowed:
        # Remove the entry we just added since the request is denied
        try:
            await r.zrem(key, f"{now}")
        except Exception:
            pass
        logger.info(
            "Rate limit exceeded: user=%s action=%s count=%d/%d",
            user_id, action, current_count, max_count,
        )

    return allowed, current_count
