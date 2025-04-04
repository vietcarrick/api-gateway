# app/models/request_log.py
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RequestLog(BaseModel):
	method: str
	path: str
	status_code: int
	response_time: float  # in ms
	client_ip: str
	user_id: Optional[int] = None
	api_key_id: Optional[int] = None
	service_id: Optional[int] = None
	headers: Dict[str, str] = Field(default_factory=dict)
	query_params: Dict[str, Any] = Field(default_factory=dict)
	request_body: Optional[Any] = None
	response_size: Optional[int] = None
	error: Optional[str] = None
	timestamp: datetime = Field(default_factory=datetime.utcnow)
	
	class Config:
		schema_extra = {
			"example": {
				"method": "GET",
				"path": "/gateway/users/1",
				"status_code": 200,
				"response_time": 145.32,
				"client_ip": "192.168.1.1",
				"user_id": 42,
				"service_id": 3,
				"headers": {"User-Agent": "Mozilla/5.0"},
				"query_params": {"include": "profile"},
				"response_size": 1024,
				"timestamp": "2023-07-10T12:34:56.789Z"
			}
		}