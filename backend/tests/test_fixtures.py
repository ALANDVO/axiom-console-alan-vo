"""Tests for fixture validation and seeding."""
import pytest
from httpx import AsyncClient

from app.schemas import FixtureContent, Governance


class TestFixtureValidation:
    """Tests for fixture content validation."""

    def test_valid_fixture_content(self):
        """Test that valid fixture content passes validation."""
        content = {
            "roles": [{"name": "user"}, {"name": "admin"}],
            "users": [{"user_id": "u1", "name": "User One", "roles": ["user"]}],
            "tools": [
                {"tool_id": "read", "name": "Read", "risk_level": "low", "tool_behavior": "read"},
                {"tool_id": "write", "name": "Write", "risk_level": "high", "tool_behavior": "write"},
            ],
            "permissions": [{"role": "user", "tools": ["read"]}, {"role": "admin", "tools": ["read", "write"]}],
            "policies": {"enforcement_point": "before_llm", "rules": []},
            "high_risk_actions": ["write"],
            "escalation_triggers": [],
            "expected_escalation_channels": [],
            "governance": {
                "version": "1.0",
                "tools": [{"tool_id": "read", "name": "Read", "risk_level": "low"}],
                "policies": {"authorization": [{"role": "user", "tools": ["read"]}]},
            },
        }
        validated = FixtureContent.validate_content(content)
        assert validated.roles[0].name == "user"
        assert validated.users[0].user_id == "u1"
        assert len(validated.tools) == 2

    def test_invalid_risk_level(self):
        """Test that invalid risk_level fails validation."""
        content = {
            "roles": [],
            "users": [],
            "tools": [{"tool_id": "t1", "name": "Tool", "risk_level": "invalid", "tool_behavior": "read"}],
            "permissions": [],
        }
        with pytest.raises(Exception):
            FixtureContent.validate_content(content)

    def test_invalid_tool_behavior(self):
        """Test that invalid tool_behavior fails validation."""
        content = {
            "roles": [],
            "users": [],
            "tools": [{"tool_id": "t1", "name": "Tool", "risk_level": "low", "tool_behavior": "invalid"}],
            "permissions": [],
        }
        with pytest.raises(Exception):
            FixtureContent.validate_content(content)

    def test_invalid_enforcement_point(self):
        """Test that invalid enforcement_point fails validation."""
        content = {
            "roles": [],
            "users": [],
            "tools": [],
            "permissions": [],
            "policies": {"enforcement_point": "invalid"},
        }
        with pytest.raises(Exception):
            FixtureContent.validate_content(content)

    def test_valid_governance(self):
        """Test valid governance structure."""
        governance = {
            "version": "1.0",
            "tools": [{"tool_id": "t1", "name": "Tool", "risk_level": "low"}],
            "policies": {
                "authorization": [{"role": "user", "tools": ["t1"]}],
                "override": {"deny_message": "Denied", "authorized_roles": ["admin"]},
                "governance_architecture": {"layers": ["auth"], "deterministic_control": True, "components": ["engine"]},
            },
        }
        validated = Governance.model_validate(governance)
        assert validated.version == "1.0"
        assert len(validated.tools) == 1

    def test_invalid_governance_risk_level(self):
        """Test invalid risk_level in governance fails."""
        governance = {
            "version": "1.0",
            "tools": [{"tool_id": "t1", "name": "Tool", "risk_level": "invalid"}],
        }
        with pytest.raises(Exception):
            Governance.model_validate(governance)


class TestFixtureAPI:
    """Tests for fixture API endpoints with validation."""

    @pytest.mark.asyncio
    async def test_create_fixture_valid_content(self, async_client):
        """Create fixture with valid content succeeds."""
        fixture_data = {
            "name": "Test Fixture",
            "version": "1.0",
            "domain": "test",
            "description": "Test fixture",
            "content": {
                "roles": [{"name": "user"}],
                "users": [{"user_id": "u1", "name": "User", "roles": ["user"]}],
                "tools": [{"tool_id": "read", "name": "Read", "risk_level": "low", "tool_behavior": "read"}],
                "permissions": [{"role": "user", "tools": ["read"]}],
                "policies": {"enforcement_point": "before_llm", "rules": []},
            },
            "governance": {"version": "1.0", "tools": [{"tool_id": "read", "name": "Read", "risk_level": "low"}]},
        }
        response = await async_client.post("/api/v1/fixtures", json=fixture_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Fixture"
        assert data["is_builtin"] is False

    @pytest.mark.asyncio
    async def test_create_fixture_invalid_content(self, async_client):
        """Create fixture with invalid content fails with 422."""
        fixture_data = {
            "name": "Invalid Fixture",
            "version": "1.0",
            "content": {
                "roles": [],
                "users": [],
                "tools": [{"tool_id": "t1", "name": "Tool", "risk_level": "invalid", "tool_behavior": "read"}],
                "permissions": [],
            },
        }
        response = await async_client.post("/api/v1/fixtures", json=fixture_data)
        assert response.status_code == 422
        assert "Invalid fixture content" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_fixture_invalid_governance(self, async_client):
        """Create fixture with invalid governance fails with 422."""
        fixture_data = {
            "name": "Invalid Governance Fixture",
            "version": "1.0",
            "content": {
                "roles": [],
                "users": [],
                "tools": [{"tool_id": "t1", "name": "Tool", "risk_level": "low", "tool_behavior": "read"}],
                "permissions": [],
            },
            "governance": {"version": "1.0", "tools": [{"tool_id": "t1", "name": "Tool", "risk_level": "invalid"}]},
        }
        response = await async_client.post("/api/v1/fixtures", json=fixture_data)
        assert response.status_code == 422
        assert "Invalid governance structure" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_fixture_validates_content(self, async_client):
        """Update fixture validates new content."""
        # Create valid fixture first
        fixture_data = {
            "name": "Update Test Fixture",
            "version": "1.0",
            "content": {
                "roles": [{"name": "user"}],
                "users": [{"user_id": "u1", "name": "User", "roles": ["user"]}],
                "tools": [{"tool_id": "read", "name": "Read", "risk_level": "low", "tool_behavior": "read"}],
                "permissions": [{"role": "user", "tools": ["read"]}],
            },
        }
        create_resp = await async_client.post("/api/v1/fixtures", json=fixture_data)
        assert create_resp.status_code == 201
        fixture_id = create_resp.json()["id"]

        # Try to update with invalid content
        update_data = {
            "content": {
                "roles": [],
                "users": [],
                "tools": [{"tool_id": "t1", "name": "Tool", "risk_level": "invalid", "tool_behavior": "read"}],
                "permissions": [],
            }
        }
        response = await async_client.patch(f"/api/v1/fixtures/{fixture_id}", json=update_data)
        assert response.status_code == 422
        assert "Invalid fixture content" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_seed_builtin_fixtures(self, async_client):
        """Seed builtin fixtures endpoint works."""
        response = await async_client.post("/api/v1/fixtures/seed")
        assert response.status_code == 201
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert data["items"][0]["is_builtin"] is True

    @pytest.mark.asyncio
    async def test_seed_builtin_idempotent(self, async_client):
        """Seeding twice doesn't duplicate fixtures."""
        await async_client.post("/api/v1/fixtures/seed")
        resp2 = await async_client.post("/api/v1/fixtures/seed")
        assert resp2.status_code == 201
        data = resp2.json()
        # Second call should create 0 new fixtures
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_builtin_fixtures(self, async_client):
        """List builtin fixtures returns seeded fixtures."""
        await async_client.post("/api/v1/fixtures/seed")
        response = await async_client.get("/api/v1/fixtures/builtin")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["is_builtin"] is True