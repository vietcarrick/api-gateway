from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from app.db.mongodb import get_mongodb
from app.schemas.log import LogFilterParams
from bson import ObjectId

logger = logging.getLogger(__name__)


async def log_request(
    method: str,
    path: str,
    status_code: int,
    response_time: float,
    client_ip: str,
    user_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    service_id: Optional[int] = None,
    headers: Dict[str, str] = None,
    query_params: Dict[str, Any] = None,
    error: Optional[str] = None,
) -> None:
    """Log a request to MongoDB."""
    try:
        mongodb = await get_mongodb()

        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time,
            "client_ip": client_ip,
            "timestamp": datetime.utcnow(),
            "headers": headers or {},
            "query_params": query_params or {},
        }

        if user_id:
            log_data["user_id"] = user_id
        if api_key_id:
            log_data["api_key_id"] = api_key_id
        if service_id:
            log_data["service_id"] = service_id
        if error:
            log_data["error"] = error

        await mongodb["request_logs"].insert_one(log_data)
    except Exception as e:
        logger.error(f"Failed to log request: {str(e)}")


async def get_logs(
    mongodb: AsyncIOMotorDatabase,
    filter_params: LogFilterParams,
) -> List[Dict[str, Any]]:
    query = {}

    if filter_params.service_id:
        query["service_id"] = filter_params.service_id
    if filter_params.user_id:
        query["user_id"] = filter_params.user_id
    if filter_params.status_code:
        query["status_code"] = filter_params.status_code
    if filter_params.method:
        query["method"] = filter_params.method
    if filter_params.path:
        query["path"] = {"$regex": filter_params.path, "$options": "i"}

    if filter_params.from_date or filter_params.to_date:
        query["timestamp"] = {}
        if filter_params.from_date:
            query["timestamp"]["$gte"] = filter_params.from_date
        if filter_params.to_date:
            query["timestamp"]["$lte"] = filter_params.to_date

    cursor = (
        mongodb["request_logs"]
        .find(query)
        .sort("timestamp", -1)
        .skip(filter_params.skip)
        .limit(filter_params.limit)
    )

    logs = []
    async for log in cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)

    return logs


async def get_log_stats(
    mongodb: AsyncIOMotorDatabase,
    service_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    match_query = {}
    if service_id:
        match_query["service_id"] = service_id

    if from_date or to_date:
        match_query["timestamp"] = {}
        if from_date:
            match_query["timestamp"]["$gte"] = from_date
        if to_date:
            match_query["timestamp"]["$lte"] = to_date

    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": None,
                "total_requests": {"$sum": 1},
                "average_response_time": {"$avg": "$response_time"},
                "success_count": {
                    "$sum": {"$cond": [{"$lt": ["$status_code", 400]}, 1, 0]}
                },
            }
        },
    ]

    result = await mongodb["request_logs"].aggregate(pipeline).to_list(1)

    if not result:
        return {
            "total_requests": 0,
            "average_response_time": 0,
            "success_rate": 0,
            "requests_per_minute": 0,
            "top_endpoints": [],
            "status_code_distribution": {},
        }

    stats = result[0]
    total = stats["total_requests"]
    success_rate = (stats["success_count"] / total) * 100 if total > 0 else 0

    time_diff = (
        (to_date - from_date).total_seconds() / 60 if from_date and to_date else 1440
    )
    requests_per_minute = total / time_diff if time_diff > 0 else 0

    endpoint_pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": {"method": "$method", "path": "$path"},
                "count": {"$sum": 1},
                "avg_time": {"$avg": "$response_time"},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]

    top_endpoints = (
        await mongodb["request_logs"].aggregate(endpoint_pipeline).to_list(5)
    )
    top_endpoints_result = []

    for endpoint in top_endpoints:
        top_endpoints_result.append(
            {
                "method": endpoint["_id"]["method"],
                "path": endpoint["_id"]["path"],
                "count": endpoint["count"],
                "avg_response_time": round(endpoint["avg_time"], 2),
            }
        )

    status_pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": {
                    "$concat": [
                        {
                            "$cond": [
                                {"$lt": ["$status_code", 200]},
                                "1xx",
                                {
                                    "$cond": [
                                        {"$lt": ["$status_code", 300]},
                                        "2xx",
                                        {
                                            "$cond": [
                                                {"$lt": ["$status_code", 400]},
                                                "3xx",
                                                {
                                                    "$cond": [
                                                        {"$lt": ["$status_code", 500]},
                                                        "4xx",
                                                        "5xx",
                                                    ]
                                                },
                                            ]
                                        },
                                    ]
                                },
                            ]
                        }
                    ]
                },
                "count": {"$sum": 1},
            }
        },
    ]

    status_results = (
        await mongodb["request_logs"].aggregate(status_pipeline).to_list(10)
    )
    status_distribution = {}

    for status in status_results:
        status_distribution[status["_id"]] = status["count"]

    return {
        "total_requests": total,
        "average_response_time": round(stats["average_response_time"], 2),
        "success_rate": round(success_rate, 2),
        "requests_per_minute": round(requests_per_minute, 2),
        "top_endpoints": top_endpoints_result,
        "status_code_distribution": status_distribution,
    }
