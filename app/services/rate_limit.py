import time
from app.db.redis_client import redis_client
from app.core.errors import RateLimitError


async def check_rate_limit(key: str, limit: int, duration: int) -> None:
    if not redis_client.client:
        return

    now = int(time.time())
    redis_key = f"rate:{key}:{now // duration}"

    count = await redis_client.client.incr(redis_key)

    if count == 1:
        await redis_client.client.expire(redis_key, duration * 2)
    if count > limit:
        retry_after = duration - (now % duration)

        ttl = await redis_client.client.ttl(redis_key)
        if ttl > 0:
            retry_after = min(retry_after, ttl)

        raise RateLimitError(
            detail=f"Rate limit exceeded. {limit} requests allowed per {duration} seconds. Retry after {retry_after} seconds.",
            retry_after=retry_after,
        )
