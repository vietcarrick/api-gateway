# app/middleware/authentication.py
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED
import logging
import jwt
from typing import Optional
from jwt.exceptions import InvalidTokenError

from app.core.config import settings
from app.core.security import ALGORITHM

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if (
            request.url.path.startswith("/auth")
            or request.url.path.startswith("/docs")
            or request.url.path.startswith("/redoc")
            or request.url.path.startswith("/openapi.json")
        ):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

        api_key = request.headers.get("X-API-Key")

        if not token and not api_key:
            return await call_next(request)

        if token:
            user_id = self._validate_token(token)
            if user_id:
                request.state.user_id = user_id

        return await call_next(request)

    def _validate_token(self, token: str) -> Optional[int]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username:
                return username
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None

        return None
