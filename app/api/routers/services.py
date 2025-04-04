from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.security import get_current_active_user
from app.db.postgres import get_db
from app.schemas.service import Service, ServiceCreate, ServiceUpdate, ServiceWithStats
from app.schemas.user import User
from app.services.service import (
    create_service,
    get_services,
    get_service,
    update_service,
    delete_service,
    get_service_with_stats,
)
from app.models.service import ServiceStatus
from app.schemas.utils.pagination import PaginatedResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=Service, status_code=status.HTTP_201_CREATED)
async def create_new_service(
    service_in: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = await create_service(db, service_in, current_user.id)
    logger.info(f"Service '{service.name}' created by user {current_user.username}")
    return service


@router.get("/", response_model=PaginatedResponse[Service])
async def read_services(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[ServiceStatus] = None,
    is_public: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    services, total = await get_services(
        db,
        user_id=current_user.id,
        skip=(page - 1) * size,
        limit=size,
        status=status,
        is_public=is_public,
    )

    pages = (total + size - 1) // size

    return PaginatedResponse(
        items=services,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )


@router.get("/{service_id}", response_model=Service)
async def read_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = await get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    if (
        service.owner_id != current_user.id
        and not service.is_public
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return service


@router.get("/{service_id}/stats", response_model=ServiceWithStats)
async def read_service_stats(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific service with usage statistics."""
    service = await get_service_with_stats(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    if (
        service.owner_id != current_user.id
        and not service.is_public
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return service


@router.put("/{service_id}", response_model=Service)
async def update_existing_service(
    service_id: int,
    service_in: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a service."""
    service = await get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    if service.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    updated_service = await update_service(db, service, service_in)
    logger.info(
        f"Service '{updated_service.name}' updated by user {current_user.username}"
    )
    return updated_service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a service."""
    service = await get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    if service.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    await delete_service(db, service_id)
    logger.info(f"Service {service_id} deleted by user {current_user.username}")
    return None
