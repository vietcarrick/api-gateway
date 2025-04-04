import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.postgres import Base


class ServiceType(str, enum.Enum):
	HTTP = "http"
	GRPC = "grpc"
	GRAPHQL = "graphql"


class ServiceStatus(str, enum.Enum):
	ACTIVE = "active"
	INACTIVE = "inactive"
	MAINTENANCE = "maintenance"


class Service(Base):
	__tablename__ = "services"
	
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, index=True, nullable=False)
	description = Column(Text, nullable=True)
	base_url = Column(String, nullable=False)
	type = Column(Enum(ServiceType), default=ServiceType.HTTP)
	status = Column(Enum(ServiceStatus), default=ServiceStatus.ACTIVE)
	is_public = Column(Boolean, default=False)
	
	# Rate limiting
	rate_limit = Column(Integer, default=60)  # requests per minute
	rate_limit_duration = Column(Integer, default=60)  # seconds
	
	# Authentication/Security
	require_authentication = Column(Boolean, default=True)
	auth_header_name = Column(String, nullable=True)
	
	# Headers to forward
	forward_headers = Column(JSON, default=list)
	
	# Owner
	owner_id = Column(Integer, ForeignKey("users.id"))
	
	# Metadata
	created_at = Column(DateTime(timezone=True), server_default=func.now())
	updated_at = Column(DateTime(timezone=True), onupdate=func.now())
	
	# Relationships
	owner = relationship("User", back_populates="services")