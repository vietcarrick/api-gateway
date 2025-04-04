from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
from contextlib import asynccontextmanager

from app.api.routers import admin, auth, monitoring, services
from app.api.gateway import router as gateway_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.middleware.authentication import AuthenticationMiddleware
from app.middleware.rate_limiting import RateLimitingMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.db.redis_client import redis_client

setup_logging()
logger = logging.getLogger("api_gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_to_mongo()
        await redis_client.connect()
        yield
    finally:
        await close_mongo_connection()
        await redis_client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API Gateway",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, **settings.CORS_CONFIG)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(AuthenticationMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

app.include_router(gateway_router, prefix="/gateway")
