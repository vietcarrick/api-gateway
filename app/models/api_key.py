# app/models/api_key.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.postgres import Base


class APIKey(Base):
	__tablename__ = "api_keys"
	
	id = Column(Integer, primary_key=True, index=True)
	key = Column(String, unique=True, index=True, nullable=False)
	name = Column(String, nullable=False)
	description = Column(Text, nullable=True)
	is_active = Column(Boolean, default=True)
	user_id = Column(Integer, ForeignKey("users.id"))
	created_at = Column(DateTime(timezone=True), server_default=func.now())
	expires_at = Column(DateTime(timezone=True), nullable=True)
	
	# Relationships
	user = relationship("User", back_populates="api_keys")