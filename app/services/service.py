from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime

from app.models.service import Service, ServiceStatus
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceWithStats
from app.db.mongodb import get_mongodb


async def create_service(
    db: AsyncSession, service_in: ServiceCreate, owner_id: int
) -> Service:
    service = Service(
        name=service_in.name,
        description=service_in.description,
        base_url=service_in.base_url,
        type=service_in.type,
        status=service_in.status,
        is_public=service_in.is_public,
        rate_limit=service_in.rate_limit,
        rate_limit_duration=service_in.rate_limit_duration,
        require_authentication=service_in.require_authentication,
        auth_header_name=service_in.auth_header_name,
        forward_headers=service_in.forward_headers,
        owner_id=owner_id,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


async def get_service(db: AsyncSession, service_id: int) -> Optional[Service]:
    query = select(Service).where(Service.id == service_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_service_by_path(
    db: AsyncSession, service_name: str, owner_id: int
) -> Optional[Service]:
    query = select(Service).where(
        Service.name == service_name, Service.owner_id == owner_id
    )
    result = await db.execute(query)
    return result.scalars().first()


async def get_services(
    db: AsyncSession,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ServiceStatus] = None,
    is_public: Optional[bool] = None,
) -> tuple[List[Service], int]:
    query = select(Service)
    count_query = select(func.count()).select_from(Service)

    if user_id is not None:
        query = query.where(Service.owner_id == user_id)
        count_query = count_query.where(Service.owner_id == user_id)
    if status is not None:
        query = query.where(Service.status == status)
        count_query = count_query.where(Service.status == status)
    if is_public is not None:
        query = query.where(Service.is_public == is_public)
        count_query = count_query.where(Service.is_public == is_public)

    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar()

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    services = result.scalars().all()

    return services, total_count


async def update_service(
    db: AsyncSession, service: Service, service_in: ServiceUpdate
) -> Service:
    for field, value in service_in.dict(exclude_unset=True).items():
        setattr(service, field, value)

    await db.commit()
    await db.refresh(service)
    return service


async def delete_service(db: AsyncSession, service_id: int) -> bool:
    stmt = delete(Service).where(Service.id == service_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def get_service_with_stats(
    db: AsyncSession, service_id: int
) -> Optional[ServiceWithStats]:
    service = await get_service(db, service_id)
    if not service:
        return None
    service_dict = {
        **{col.name: getattr(service, col.name) for col in service.__table__.columns},
        "total_requests": 0,
        "success_rate": 0.0,
        "avg_response_time": 0.0,
    }

    mongodb = await get_mongodb()

    pipeline = [
        {"$match": {"service_id": service_id}},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "success_count": {
                    "$sum": {"$cond": [{"$lt": ["$status_code", 400]}, 1, 0]}
                },
                "avg_response_time": {"$avg": "$response_time"},
            }
        },
    ]

    result = await mongodb["request_logs"].aggregate(pipeline).to_list(1)

    if result:
        stats = result[0]
        service_dict["total_requests"] = stats["total"]
        service_dict["success_rate"] = (
            round((stats["success_count"] / stats["total"]) * 100, 2)
            if stats["total"] > 0
            else 0.0
        )
        service_dict["avg_response_time"] = round(stats["avg_response_time"], 2)

    return ServiceWithStats(**service_dict)
