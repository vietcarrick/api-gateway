from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import logging
from typing import Optional
import time

from app.core.errors import ServiceNotFoundError, ProxyError, ServiceUnavailableError
from app.core.security import get_current_user, validate_api_key
from app.db.postgres import get_db
from app.models.user import User
from app.services.service import get_service_by_path
from app.services.proxy import proxy_request
from app.services.rate_limit import check_rate_limit
from app.services.log_service import log_request

router = APIRouter()
logger = logging.getLogger(__name__)


@router.api_route(
    "/{service_name}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
async def gateway_endpoint(
    request: Request,
    service_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    start_time = time.time()
    client_ip = request.client.host

    service = await get_service_by_path(db, service_name, current_user.id)
    if not service:
        logger.warning(f"Service not found: {service_name}")
        raise ServiceNotFoundError(detail=f"Service '{service_name}' not found")

    if service.status != "active":
        logger.warning(f"Service {service_name} is not active: {service.status}")
        raise ServiceUnavailableError(
            detail=f"Service '{service_name}' is {service.status}"
        )

    if service.require_authentication and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = current_user.id if current_user else None

    rate_limit_key = f"service:{service.id}:user:{user_id or 'anonymous'}"
    await check_rate_limit(
        rate_limit_key, service.rate_limit, service.rate_limit_duration
    )

    try:
        response = await proxy_request(
            request=request, service=service, user=current_user
        )

        process_time = time.time() - start_time

        await log_request(
            method=request.method,
            path=service.base_url,
            status_code=response.status_code,
            response_time=process_time * 1000,
            client_ip=client_ip,
            user_id=user_id,
            service_id=service.id,
            headers=dict(request.headers),
            query_params=dict(request.query_params),
        )
        return response

    except httpx.RequestError as e:
        logger.error(f"Error proxying request to {service_name}: {str(e)}")
        process_time = time.time() - start_time

        await log_request(
            method=request.method,
            path=service.base_url,
            status_code=status.HTTP_502_BAD_GATEWAY,
            response_time=process_time * 1000,
            client_ip=client_ip,
            user_id=user_id,
            service_id=service.id,
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            error=str(e),
        )

        raise ProxyError(detail=f"Error connecting to service: {str(e)}")

    except Exception as e:
        logger.exception(f"Unexpected error in gateway: {str(e)}")
        process_time = time.time() - start_time

        await log_request(
            method=request.method,
            path=service.base_url,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            response_time=process_time * 1000,
            client_ip=client_ip,
            user_id=user_id,
            service_id=service.id,
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            error=str(e),
        )

        raise ProxyError(
            detail="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
