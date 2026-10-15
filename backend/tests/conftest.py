"""Shared test fixtures and configuration."""
import os
import sys
import tempfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import create_app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def _build_engine():
    """Create a test engine with StaticPool for in-memory SQLite sharing."""
    return create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest_asyncio.fixture(scope="session", autouse=True)
async def test_engine():
    """Create tables on a shared in-memory engine for the whole session."""
    engine = _build_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Provide a test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(test_engine):
    """Create a test client with override_get_db using the shared test engine."""
    test_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with test_session() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_tables(test_engine):
    """Delete all rows from every table after each test."""
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.exec_driver_sql(f"DELETE FROM {table.name}")


@pytest.fixture
def sample_fixture():
    """Sample fixture for testing."""
    return {
        "metadata": {
            "name": "Test Fixture",
            "version": "1.0",
            "domain": "customer_support",
        },
        "roles": [
            {"name": "user", "description": "Standard user"},
            {"name": "admin", "description": "Administrator"},
        ],
        "users": [
            {"user_id": "u1", "name": "User One", "roles": ["user"]},
            {"user_id": "u2", "name": "User Two", "roles": ["user"]},
            {"user_id": "u3", "name": "Admin One", "roles": ["admin"]},
        ],
        "tools": [
            {"tool_id": "read_record", "name": "Read Record", "category": "read", "risk_level": "low", "tool_behavior": "read"},
            {"tool_id": "write_record", "name": "Write Record", "category": "write", "risk_level": "high", "tool_behavior": "write"},
            {"tool_id": "delete_record", "name": "Delete Record", "category": "delete", "risk_level": "critical", "tool_behavior": "destructive"},
        ],
        "permissions": [
            {"role": "user", "tools": ["read_record"]},
            {"role": "admin", "tools": ["read_record", "write_record", "delete_record"]},
        ],
        "policies": {
            "enforcement_point": "before_llm",
            "rules": [
                {"id": "access_control", "name": "Role-Based Access Control", "description": "A user may only call tools assigned to their role."}
            ],
        },
        "high_risk_actions": ["delete_record"],
        "escalation_triggers": ["Customer requests account deletion", "Payment dispute over 500 EUR"],
        "expected_escalation_channels": ["email", "ticket"],
        "governance": {
            "version": "1.0.0",
            "tools": [
                {"tool_id": "read_record", "name": "Read Record", "risk_level": "low"},
                {"tool_id": "write_record", "name": "Write Record", "risk_level": "high"},
                {"tool_id": "delete_record", "name": "Delete Record", "risk_level": "critical"},
            ],
            "policies": {
                "authorization": [
                    {"role": "user", "tools": ["read_record"]},
                    {"role": "admin", "tools": ["read_record", "write_record", "delete_record"]},
                ],
                "override": {"deny_message": "Request denied by policy", "authorized_roles": ["admin"]},
                "governance_architecture": {
                    "layers": ["authorization", "audit"],
                    "deterministic_control": True,
                    "components": ["policy_engine", "audit_logger"],
                },
            },
        },
    }