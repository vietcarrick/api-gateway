from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import uuid
import logging

from app.core.config import settings
from app.core.security import (
    create_access_token,
    verify_password,
    get_current_active_user,
    get_current_admin_user,
)
from app.db.postgres import get_db
from app.schemas.auth import Token, APIKeyCreate, APIKeyResponse
from app.schemas.user import UserCreate, User, UserUpdate
from app.services.auth import (
    get_user_by_username,
    create_user,
    create_api_key,
    get_user_api_keys,
    deactivate_api_key,
)
from app.schemas.utils.pagination import PaginatedResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )

    logger.info(f"User {user.username} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    db_user = await get_user_by_username(db, username=user_in.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    user = await create_user(db, user_in)
    logger.info(f"New user created: {user.username}")
    return user


@router.post(
    "/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_api_key(
    api_key_in: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    api_key_value = str(uuid.uuid4())
    api_key = await create_api_key(db, current_user.id, api_key_in, api_key_value)

    logger.info(f"New API key created for user {current_user.username}")
    return APIKeyResponse.model_validate(api_key)


@router.get("/api-keys", response_model=PaginatedResponse[APIKeyResponse])
async def read_api_keys(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    api_keys, total = await get_user_api_keys(
        db, current_user.id, skip=(page - 1) * size, limit=size
    )
    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=api_keys,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await deactivate_api_key(db, api_key_id, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    logger.info(f"API key {api_key_id} deactivated by user {current_user.username}")
    return None
