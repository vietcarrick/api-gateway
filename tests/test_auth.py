import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_login_valid_credentials(client: AsyncClient, test_user: User):
    """Test login with valid credentials."""
    response = await client.post(
        "/api/auth/login",
        data={"username": test_user.username, "password": "password123"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/auth/login",
        data={"username": test_user.username, "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, admin_token: str):
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "newpassword123",
            "role": "DEVELOPER",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    user_data = response.json()
    assert user_data["username"] == "newuser"
    assert user_data["email"] == "newuser@example.com"
    assert "id" in user_data
    assert "hashed_password" not in user_data


@pytest.mark.asyncio
async def test_register_user_unauthorized(client: AsyncClient):
    """Test registering a new user without admin privileges."""
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "newpassword123",
            "role": "DEVELOPER",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient, user_token: str):
    response = await client.post(
        "/api/auth/api-keys",
        json={
            "name": "New API Key",
            "description": "Description for new API key",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    api_key_data = response.json()
    assert api_key_data["name"] == "New API Key"
    assert "key" in api_key_data
    assert api_key_data["is_active"] is True


@pytest.mark.asyncio
async def test_get_api_keys(client: AsyncClient, user_token: str, test_api_key):
    response = await client.get(
        "/api/auth/api-keys",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1
    assert data["items"][0]["name"] == test_api_key.name


@pytest.mark.asyncio
async def test_delete_api_key(client: AsyncClient, user_token: str, test_api_key):
    response = await client.delete(
        f"/api/auth/api-keys/{test_api_key.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
