from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.models.user import User
from app.models.api_key import APIKey
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.auth import APIKeyCreate


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> tuple[List[User], int]:
    query = select(User).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    count_query = select(func.count()).select_from(User)
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return users, total


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    from app.core.security import get_password_hash

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=user_in.is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, user_in: UserUpdate) -> User:
    from app.core.security import get_password_hash

    if user_in.email is not None:
        user.email = user_in.email
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.password is not None:
        user.hashed_password = get_password_hash(user_in.password)
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    stmt = delete(User).where(User.id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def create_api_key(
    db: AsyncSession, user_id: int, api_key_in: APIKeyCreate, api_key_value: str
) -> APIKey:
    expires_at = (
        datetime.fromisoformat(api_key_in.expires_at) if api_key_in.expires_at else None
    )

    api_key = APIKey(
        key=api_key_value,
        name=api_key_in.name,
        description=api_key_in.description,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def get_user_api_keys(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
) -> tuple[List[APIKey], int]:
    query = select(APIKey).where(APIKey.user_id == user_id).offset(skip).limit(limit)
    result = await db.execute(query)
    api_keys = result.scalars().all()

    count_query = (
        select(func.count()).select_from(APIKey).where(APIKey.user_id == user_id)
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return api_keys, total


async def get_api_key(db: AsyncSession, api_key: str) -> Optional[APIKey]:
    query = select(APIKey).where(APIKey.key == api_key)
    result = await db.execute(query)
    return result.scalars().first()


async def deactivate_api_key(db: AsyncSession, api_key_id: int, user_id: int) -> bool:
    query = select(APIKey).where(APIKey.id == api_key_id, APIKey.user_id == user_id)
    result = await db.execute(query)
    api_key = result.scalars().first()

    if not api_key:
        return False

    api_key.is_active = False
    await db.commit()
    return True
