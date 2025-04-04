from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    expires_at: Optional[str] = None

    @field_validator("expires_at")
    def check_expiry_date(cls, value):
        if value is None:
            return value

        try:
            expiry_date = datetime.fromisoformat(value)
            if expiry_date < datetime.utcnow():
                raise ValueError("Expiry date cannot be in the past")
            return value
        except ValueError as e:
            raise e


class APIKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    expires_at: datetime | None = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str
