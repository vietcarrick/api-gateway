import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_get_all_users(client: AsyncClient, admin_token: str, test_user: User):
    response = await client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 2


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, admin_token: str, test_user: User):
    response = await client.get(
        f"/api/admin/users/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data["id"] == test_user.id
    assert user_data["username"] == test_user.username


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, admin_token: str, test_user: User):
    response = await client.put(
        f"/api/admin/users/{test_user.id}",
        json={
            "full_name": "Updated User Name",
            "role": "SERVICE_OWNER",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data["full_name"] == "Updated User Name"
    assert user_data["role"] == "SERVICE_OWNER"
