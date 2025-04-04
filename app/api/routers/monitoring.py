from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.security import get_current_active_user, get_current_admin_user
from app.db.postgres import get_db
from app.db.mongodb import get_mongodb
from app.schemas.user import User
from app.schemas.log import LogFilterParams, LogResponse, LogStatsResponse
from app.services.log_service import get_logs, get_log_stats

router = APIRouter()


@router.get("/logs", response_model=List[LogResponse])
async def read_logs(
    service_id: Optional[int] = None,
    status_code: Optional[int] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: User = Depends(get_current_admin_user),
):
    filter_params = LogFilterParams(
        service_id=service_id,
        status_code=status_code,
        method=method,
        path=path,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        skip=skip,
    )

    logs = await get_logs(mongodb, filter_params)
    return logs


@router.get("/stats", response_model=LogStatsResponse)
async def read_log_stats(
    service_id: Optional[int] = None,
    from_date: Optional[datetime] = Query(
        None, description="From date (default: 24 hours ago)"
    ),
    to_date: Optional[datetime] = Query(None, description="To date (default: now)"),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: User = Depends(get_current_active_user),
):
    if not from_date:
        from_date = datetime.utcnow() - timedelta(days=1)
    if not to_date:
        to_date = datetime.utcnow()

    stats = await get_log_stats(mongodb, service_id, from_date, to_date)
    return stats
