import pytest
from httpx import AsyncClient
from fastapi import status
from app.models.service import Service


@pytest.mark.asyncio
async def test_create_service(client: AsyncClient, user_token: str):
    response = await client.post(
        "/api/services/",
        json={
            "name": "new-service",
            "description": "New service for testing",
            "base_url": "http://new-service:8080",
            "type": "http",
            "status": "active",
            "is_public": False,
            "rate_limit": 100,
            "rate_limit_duration": 60,
            "require_authentication": True,
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    service_data = response.json()
    assert service_data["name"] == "new-service"
    assert service_data["description"] == "New service for testing"
    assert "id" in service_data


@pytest.mark.asyncio
async def test_get_all_services(
    client: AsyncClient, user_token: str, test_service: Service
):
    response = await client.get(
        "/api/services/",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_get_service_by_id(
    client: AsyncClient, user_token: str, test_service: Service
):
    response = await client.get(
        f"/api/services/{test_service.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    service_data = response.json()
    assert service_data["id"] == test_service.id
    assert service_data["name"] == test_service.name


@pytest.mark.asyncio
async def test_update_service(
    client: AsyncClient, user_token: str, test_service: Service
):
    response = await client.put(
        f"/api/services/{test_service.id}",
        json={
            "name": "updated-service",
            "description": "Updated service description",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    service_data = response.json()
    assert service_data["name"] == "updated-service"
    assert service_data["description"] == "Updated service description"


@pytest.mark.asyncio
async def test_delete_service(
    client: AsyncClient, user_token: str, test_service: Service
):
    response = await client.delete(
        f"/api/services/{test_service.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
