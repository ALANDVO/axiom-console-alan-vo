import os
import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import Message, ProviderCapabilities


class TestAnthropicProvider:
    """Tests for Anthropic provider adapter."""

    def test_provider_type(self):
        """Test provider type identifier."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "test-key"})
        assert provider.provider_type == "anthropic"

    def test_capabilities_known_model(self):
        """Test capabilities for known model."""
        provider = AnthropicProvider({"model": "claude-3-5-sonnet-20241022", "api_key": "test-key"})
        caps = provider.capabilities
        assert caps.supports_tools is True
        assert caps.supports_streaming is True
        assert caps.supports_system_prompt is True
        assert caps.max_tokens == 8192

    def test_capabilities_unknown_model(self):
        """Test capabilities for unknown model defaults."""
        provider = AnthropicProvider({"model": "unknown-model", "api_key": "test-key"})
        caps = provider.capabilities
        assert caps.supports_tools is False
        assert caps.supports_streaming is False
        assert caps.supports_system_prompt is True
        assert caps.max_tokens is None

    def test_missing_api_key_raises(self):
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="Anthropic API key required"):
            with patch.dict(os.environ, {}, clear=True):
                AnthropicProvider({"model": "claude-3-5-haiku-20241022"})

    def test_api_key_from_config(self):
        """Test API key can be passed in config."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "config-key"})
        assert provider.api_key == "config-key"

    def test_api_key_from_env(self):
        """Test API key from environment variable."""
        with patch.dict(os.environ, {"LLM_API_KEY": "env-key"}):
            provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022"})
            assert provider.api_key == "env-key"

    def test_config_summary_no_secrets(self):
        """Test config summary does not include API key."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "secret-key"})
        summary = provider.get_config_summary()
        assert summary["type"] == "anthropic"
        assert summary["model"] == "claude-3-5-haiku-20241022"
        assert "secret-key" not in str(summary)

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check returns True on success."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "test-key"})
        provider.client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 400  # Expected for minimal request
        provider.client.post.return_value = mock_response

        result = await provider.health_check()
        assert result is True
        provider.client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check returns False on failure."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "test-key"})
        provider.client = AsyncMock()
        provider.client.post.side_effect = Exception("Network error")

        result = await provider.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message send."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "test-key"})
        provider.client = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "model": "claude-3-5-haiku-20241022",
            "content": [{"type": "text", "text": "Hello! How can I help you?"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
        provider.client.post.return_value = mock_response

        messages = [Message(role="user", content="Hello")]
        response = await provider.send_message(messages)

        assert response.content == "Hello! How can I help you?"
        assert response.tool_calls == []
        assert response.metadata["model"] == "claude-3-5-haiku-20241022"
        assert response.metadata["stop_reason"] == "end_turn"
        assert response.metadata["usage"] == {"input_tokens": 10, "output_tokens": 5}

    @pytest.mark.asyncio
    async def test_send_message_with_tools(self):
        """Test message send with tool calls."""
        provider = AnthropicProvider({"model": "claude-3-5-sonnet-20241022", "api_key": "test-key"})
        provider.client = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "model": "claude-3-5-sonnet-20241022",
            "content": [
                {"type": "text", "text": "I'll check the weather for you."},
                {"type": "tool_use", "id": "toolu_123", "name": "get_weather", "input": {"location": "San Francisco"}},
            ],
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 20, "output_tokens": 30},
        }
        provider.client.post.return_value = mock_response

        messages = [Message(role="user", content="What's the weather in San Francisco?")]
        tools = [{"name": "get_weather", "description": "Get weather", "input_schema": {"type": "object", "properties": {"location": {"type": "string"}}}}]
        response = await provider.send_message(messages, tools=tools)

        assert response.content == "I'll check the weather for you."
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].id == "toolu_123"
        assert response.tool_calls[0].name == "get_weather"
        assert response.tool_calls[0].arguments == {"location": "San Francisco"}
        assert response.metadata["stop_reason"] == "tool_use"

    @pytest.mark.asyncio
    async def test_send_message_auth_error(self):
        """Test authentication error handling."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "test-key"})
        provider.client = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        import httpx
        provider.client.post.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=mock_response
        )

        messages = [Message(role="user", content="Hello")]
        with pytest.raises(RuntimeError, match="Anthropic authentication failed"):
            await provider.send_message(messages)

    @pytest.mark.asyncio
    async def test_send_message_rate_limit(self):
        """Test rate limit error handling."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "test-key"})
        provider.client = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 429
        import httpx
        provider.client.post.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests", request=MagicMock(), response=mock_response
        )

        messages = [Message(role="user", content="Hello")]
        with pytest.raises(RuntimeError, match="Anthropic rate limit exceeded"):
            await provider.send_message(messages)

    @pytest.mark.asyncio
    async def test_send_message_server_error(self):
        """Test server error handling."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "test-key"})
        provider.client = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 500
        import httpx
        provider.client.post.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", request=MagicMock(), response=mock_response
        )

        messages = [Message(role="user", content="Hello")]
        with pytest.raises(RuntimeError, match="Anthropic server error"):
            await provider.send_message(messages)

    @pytest.mark.asyncio
    async def test_send_message_network_error(self):
        """Test network error handling."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "test-key"})
        provider.client = AsyncMock()
        provider.client.post.side_effect = httpx.RequestError("Connection failed")

        messages = [Message(role="user", content="Hello")]
        with pytest.raises(RuntimeError, match="Anthropic request failed: RequestError"):
            await provider.send_message(messages)

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test closing the HTTP client."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "test-key"})
        provider.client = AsyncMock()

        await provider.close()
        provider.client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager."""
        provider = AnthropicProvider({"model": "claude-3-5-haiku-20241022", "api_key": "test-key"})
        provider.client = AsyncMock()

        async with provider as p:
            assert p is provider

        provider.client.aclose.assert_called_once()
