from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class LogFilterParams(BaseModel):
    service_id: Optional[int] = None
    user_id: Optional[int] = None
    status_code: Optional[int] = None
    method: Optional[str] = None
    path: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = 100
    skip: int = 0


class LogResponse(BaseModel):
    id: str = Field(..., alias="_id")
    method: str
    path: str
    status_code: int
    response_time: float
    client_ip: str
    user_id: Optional[int] = None
    api_key_id: Optional[int] = None
    service_id: Optional[int] = None
    timestamp: datetime
    headers: Dict[str, str] = Field(default_factory=dict)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    class Config:
        populate_by_name = True


class LogStatsResponse(BaseModel):
    total_requests: int
    average_response_time: float
    success_rate: float
    requests_per_minute: float
    top_endpoints: List[Dict[str, Any]]
    status_code_distribution: Dict[str, int]