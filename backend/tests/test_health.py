import pytest


@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "environment" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_readiness_check(async_client):
    response = await async_client.get("/health/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data