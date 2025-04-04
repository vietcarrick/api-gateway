from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models.service import ServiceType, ServiceStatus


class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_url: str
    type: ServiceType = ServiceType.HTTP
    status: ServiceStatus = ServiceStatus.ACTIVE
    is_public: bool = False
    rate_limit: int = 60
    rate_limit_duration: int = 60
    require_authentication: bool = True
    auth_header_name: Optional[str] = None
    forward_headers: List[str] = Field(default_factory=list)

    @field_validator("base_url")
    def base_url_must_be_valid(cls, v):
        if not v.startswith(("http://", "https://", "grpc://")):
            raise ValueError("base_url must be a valid URL")
        return v


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    type: Optional[ServiceType] = None
    status: Optional[ServiceStatus] = None
    is_public: Optional[bool] = None
    rate_limit: Optional[int] = None
    rate_limit_duration: Optional[int] = None
    require_authentication: Optional[bool] = None
    auth_header_name: Optional[str] = None
    forward_headers: Optional[List[str]] = None


class ServiceInDBBase(ServiceBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Service(ServiceInDBBase):
    pass


class ServiceWithStats(Service):
    total_requests: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
