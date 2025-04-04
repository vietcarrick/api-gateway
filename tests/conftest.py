# tests/conftest.py
import asyncio
import os
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import jwt
from datetime import datetime, timedelta, timezone

from app.db.postgres import Base, get_db
from app.main import app
from app.core.config import settings
from app.core.security import ALGORITHM, create_access_token
from app.models.user import User, UserRole
from app.models.service import Service, ServiceType, ServiceStatus
from app.models.api_key import APIKey

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/api_gateway_test"
)

engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db() -> AsyncGenerator:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def app_fixture() -> FastAPI:
    return app


@pytest_asyncio.fixture
async def client(app_fixture: FastAPI, db: AsyncSession) -> AsyncGenerator:
    async def override_get_db():
        try:
            yield db
        finally:
            pass

    app_fixture.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app_fixture, base_url="http://test") as client:
        yield client
    app_fixture.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_admin(db: AsyncSession) -> User:
    from app.core.security import get_password_hash

    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("admin123"),
        role="ADMIN",
        is_active=True,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    from app.core.security import get_password_hash

    user = User(
        username="testuser",
        email="user@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("password123"),
        role="DEVELOPER",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_service(db: AsyncSession, test_user: User) -> Service:
    service = Service(
        name="test-service",
        description="Test Service",
        base_url="http://localhost:8080",
        type="HTTP",
        status="ACTIVE",
        is_public=False,
        rate_limit=100,
        rate_limit_duration=60,
        require_authentication=True,
        owner_id=test_user.id,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@pytest_asyncio.fixture
async def test_api_key(db: AsyncSession, test_user: User) -> APIKey:
    import uuid

    api_key = APIKey(
        key=str(uuid.uuid4()),
        name="Test API Key",
        description="Test API Key Description",
        is_active=True,
        user_id=test_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key


@pytest.fixture
def admin_token(test_admin: User) -> str:
    return create_access_token(
        data={"sub": test_admin.username},
        expires_delta=timedelta(minutes=30),
    )


@pytest.fixture
def user_token(test_user: User) -> str:
    return create_access_token(
        data={"sub": test_user.username},
        expires_delta=timedelta(minutes=30),
    )
