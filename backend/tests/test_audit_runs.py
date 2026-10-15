import pytest


@pytest.mark.asyncio
async def test_create_audit_run(async_client, sample_fixture):
    """Create a fixture then an audit run via the API."""
    fixture_data = {
        "name": "Test Fixture",
        "version": "1.0",
        "domain": "customer_support",
        "description": "Test fixture",
        "content": sample_fixture,
        "governance": sample_fixture.get("governance"),
    }
    fixture_resp = await async_client.post("/api/v1/fixtures", json=fixture_data)
    assert fixture_resp.status_code == 201
    fixture_id = fixture_resp.json()["id"]

    run_data = {
        "name": "Test Audit Run",
        "description": "Test run",
        "fixture_id": fixture_id,
        "provider_config": {
            "type": "mock",
            "model": "mock-model",
            "timeout_seconds": 30,
        },
        "judge_config": None,
        "suite": "essential",
        "eval_mode": "self",
    }
    response = await async_client.post("/api/v1/audit/runs", json=run_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Audit Run"
    assert data["status"] == "pending"
    assert data["fixture_id"] == fixture_id
    assert data["provider_config"]["type"] == "mock"


@pytest.mark.asyncio
async def test_create_audit_run_invalid_fixture(async_client):
    """Ensure creating an audit run with a nonexistent fixture returns 404."""
    from uuid import uuid4

    run_data = {
        "name": "Bad Run",
        "description": "Should fail",
        "fixture_id": str(uuid4()),
        "provider_config": {"type": "mock", "timeout_seconds": 30},
        "judge_config": None,
        "suite": "essential",
        "eval_mode": "self",
    }
    response = await async_client.post("/api/v1/audit/runs", json=run_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_audit_runs(async_client):
    """List audit runs returns paginated structure."""
    response = await async_client.get("/api/v1/audit/runs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


@pytest.mark.asyncio
async def test_get_audit_run_not_found(async_client):
    """Getting a nonexistent audit run returns 404."""
    from uuid import uuid4

    response = await async_client.get(f"/api/v1/audit/runs/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_and_get_audit_run(async_client, sample_fixture):
    """Create a fixture and audit run, then retrieve it."""
    fixture_data = {
        "name": "GetTestFixture",
        "version": "1.0",
        "domain": "test",
        "description": "For retrieval test",
        "content": sample_fixture,
        "governance": None,
    }
    fixture_resp = await async_client.post("/api/v1/fixtures", json=fixture_data)
    assert fixture_resp.status_code == 201
    fixture_id = fixture_resp.json()["id"]

    run_data = {
        "name": "Retrieval Run",
        "description": "Test",
        "fixture_id": fixture_id,
        "provider_config": {"type": "mock", "model": "mock", "timeout_seconds": 30},
        "judge_config": None,
        "suite": "smoke",
        "eval_mode": "self",
    }
    create_resp = await async_client.post("/api/v1/audit/runs", json=run_data)
    assert create_resp.status_code == 201
    run_id = create_resp.json()["id"]

    get_resp = await async_client.get(f"/api/v1/audit/runs/{run_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == run_id
    assert data["name"] == "Retrieval Run"
    assert data["status"] == "completed"