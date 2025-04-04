from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import logging
from app.db.redis_client import redis_client
import time

logger = logging.getLogger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if (
            request.url.path.startswith("/api/docs")
            or request.url.path.startswith("/api/redoc")
            or request.url.path.startswith("/api/openapi.json")
            or request.url.path == "/api/health"
        ):
            return await call_next(request)

        client_id = self._get_client_id(request)

        is_limited, retry_after = await self._is_rate_limited(client_id)
        if is_limited:
            headers = {"Retry-After": str(retry_after)}
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers=headers,
            )

        return await call_next(request)

    def _get_client_id(self, request: Request) -> str:
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"

        return f"ip:{request.client.host}"

    async def _is_rate_limited(self, client_id: str) -> tuple[bool, int]:
        now = int(time.time())
        window_key = f"ratelimit:{client_id}:{now // 60}"

        if not redis_client.client:
            return False, 0

        count = await redis_client.client.incr(window_key)
        if count == 1:
            await redis_client.client.expire(window_key, 120)
        limit = 120

        if count > limit:
            retry_after = 60 - (now % 60)
            return True, retry_after

        return False, 0
