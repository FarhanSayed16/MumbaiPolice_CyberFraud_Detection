import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health_endpoint(async_client: AsyncClient):
    """
    Verify /health returns 200 OK and valid schema structure.
    """
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "project_name" in data
    assert "services" in data
    assert "postgres" in data["services"]
    assert "neo4j" in data["services"]
    assert "redis" in data["services"]


@pytest.mark.asyncio
async def test_api_v1_health_endpoint(async_client: AsyncClient):
    """
    Verify /api/v1/health returns 200 OK.
    """
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "Trace-X"


@pytest.mark.asyncio
async def test_cases_endpoint_unauthorized(async_client: AsyncClient):
    """
    Verify /api/v1/cases enforces RBAC authentication (`Sub-phase 6.1`).
    """
    response = await async_client.get("/api/v1/cases")
    assert response.status_code == 401

