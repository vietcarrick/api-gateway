from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
from typing import Callable
import json

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            self._log_request(request, response, process_time)

            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.exception(f"Request failed: {str(e)}")
            raise

    def _log_request(self, request: Request, response: Response, process_time: float):
        """Log request details."""
        if request.url.path.startswith(
            ("/static/", "/api/docs", "/api/redoc", "/api/openapi.json")
        ):
            return

        log_dict = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
            "client_ip": request.client.host,
        }

        if request.query_params:
            log_dict["query_params"] = dict(request.query_params)

        if hasattr(request.state, "user_id") and request.state.user_id:
            log_dict["user_id"] = request.state.user_id

        logger.info(json.dumps(log_dict))
