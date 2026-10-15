import pytest

from app.services.providers.mock import MockProvider, MockProviderWithFixtures
from app.services.providers.base import Message


@pytest.mark.asyncio
async def test_mock_provider_health_check():
    provider = MockProvider({"model": "mock", "seed": 42})
    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_mock_provider_send_message():
    provider = MockProvider({"model": "mock", "seed": 42})
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello, world!"),
    ]
    response = await provider.send_message(messages)
    assert response.content is not None
    assert len(response.content) > 0
    assert response.metadata.get("mock") is True


@pytest.mark.asyncio
async def test_mock_provider_deterministic():
    """Test that same seed produces same results."""
    provider1 = MockProvider({"model": "mock", "seed": 42})
    provider2 = MockProvider({"model": "mock", "seed": 42})
    
    messages = [
        Message(role="user", content="Test message"),
    ]
    
    resp1 = await provider1.send_message(messages)
    resp2 = await provider2.send_message(messages)
    
    assert resp1.content == resp2.content
    assert resp1.metadata["msg_hash"] == resp2.metadata["msg_hash"]


@pytest.mark.asyncio
async def test_mock_provider_different_seeds():
    """Test that different seeds produce different results."""
    provider1 = MockProvider({"model": "mock", "seed": 42})
    provider2 = MockProvider({"model": "mock", "seed": 123})
    
    messages = [
        Message(role="user", content="Test message"),
    ]
    
    resp1 = await provider1.send_message(messages)
    resp2 = await provider2.send_message(messages)
    
    # Different seeds should produce different msg_hash
    assert resp1.metadata["msg_hash"] != resp2.metadata["msg_hash"]


@pytest.mark.asyncio
async def test_mock_provider_with_tools():
    provider = MockProvider({"model": "mock", "seed": 42})
    messages = [
        Message(role="user", content="Please read a record"),
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_record",
                "description": "Read a record",
                "parameters": {"type": "object", "properties": {"record_id": {"type": "string"}}},
            },
        },
    ]
    response = await provider.send_message(messages, tools=tools)
    # Tool call may or may not happen based on deterministic logic
    assert response.content is not None


@pytest.mark.asyncio
async def test_mock_provider_with_fixtures(sample_fixture):
    provider = MockProviderWithFixtures({"model": "mock", "seed": 42}, sample_fixture)
    
    # Test permission check
    assert provider.check_permission("u1", "read_record") is True  # user has read_record
    assert provider.check_permission("u1", "write_record") is False  # user doesn't have write_record
    assert provider.check_permission("u3", "write_record") is True  # admin has write_record
    assert provider.check_permission("u3", "delete_record") is True  # admin has delete_record


@pytest.mark.asyncio
async def test_provider_registry():
    from app.services.providers import ProviderRegistry
    
    providers = ProviderRegistry.list_providers()
    assert "mock" in providers
    assert "mock_with_fixtures" in providers
    
    provider = ProviderRegistry.create_provider("mock", {"model": "test"})
    assert isinstance(provider, MockProvider)
    
    provider2 = ProviderRegistry.create_provider("mock_with_fixtures", {"model": "test"}, {})
    assert isinstance(provider2, MockProviderWithFixtures)