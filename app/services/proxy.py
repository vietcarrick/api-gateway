from fastapi import Request
from fastapi.responses import JSONResponse
import httpx
from typing import Dict, Optional
import logging
from urllib.parse import urljoin
from app.models.service import Service
from app.models.user import User
from app.models.api_key import APIKey
from app.core.config import settings
from app.core.errors import ProxyError

logger = logging.getLogger(__name__)


async def proxy_request(
    request: Request,
    service: Service,
    user: Optional[User] = None,
) -> JSONResponse:
    body = await request.body()
    headers = prepare_headers(request, service, user)
    params = dict(request.query_params)

    try:
        async with httpx.AsyncClient(timeout=settings.PROXY_TIMEOUT) as client:
            response = await client.request(
                method=request.method,
                url=service.base_url,
                headers=headers,
                params=params,
                content=body,
            )

            return JSONResponse(
                content=response.json(),
                status_code=response.status_code,
                headers={"Content-Type": "application/json"},
            )

    except httpx.TimeoutException:
        logger.error(f"Timeout when connecting to {service.base_url}")
        raise ProxyError(detail="Service timeout")
    except httpx.RequestError as e:
        logger.error(f"Error connecting to {service.base_url}: {str(e)}")
        raise ProxyError(detail=f"Connection error: {str(e)}")


def prepare_headers(
    request: Request,
    service: Service,
    user: Optional[User] = None,
    api_key: Optional[APIKey] = None,
) -> Dict[str, str]:
    """Prepare headers to be forwarded to the target service."""
    headers = dict(request.headers)
    headers.pop("host", None)

    if service.forward_headers:
        headers = {
            k: v for k, v in headers.items() if k.lower() in service.forward_headers
        }

    if service.require_authentication and service.auth_header_name:
        if user:
            headers[service.auth_header_name] = str(user.id)
        elif api_key:
            headers[service.auth_header_name] = f"ApiKey {api_key.key}"

    headers["X-API-Gateway"] = "true"

    return headers
