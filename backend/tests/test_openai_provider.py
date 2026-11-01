import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.providers.openai import OpenAIProvider
from app.services.providers.base import Message, ProviderCapabilities


class TestOpenAIProvider:
    """Tests for OpenAI provider adapter."""

    def test_provider_type(self):
        """Test provider type identifier."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            assert provider.provider_type == "openai"

    def test_capabilities_known_model(self):
        """Test capabilities for known model."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o"})
            caps = provider.capabilities
            assert caps.supports_tools is True
            assert caps.supports_streaming is True
            assert caps.supports_system_prompt is True
            assert caps.max_tokens == 4096

    def test_capabilities_unknown_model(self):
        """Test capabilities for unknown model defaults."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "unknown-model"})
            caps = provider.capabilities
            assert caps.supports_tools is False
            assert caps.supports_streaming is False
            assert caps.supports_system_prompt is True
            assert caps.max_tokens is None

    def test_missing_api_key_raises(self):
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                OpenAIProvider({"model": "gpt-4o-mini"})

    def test_api_key_from_config(self):
        """Test API key can be passed in config."""
        provider = OpenAIProvider({"model": "gpt-4o-mini", "api_key": "config-key"})
        assert provider.api_key == "config-key"

    def test_api_key_from_env(self):
        """Test API key from environment variable."""
        with patch.dict(os.environ, {"LLM_API_KEY": "env-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            assert provider.api_key == "env-key"

    def test_config_summary_no_secrets(self):
        """Test config summary does not include API key."""
        with patch.dict(os.environ, {"LLM_API_KEY": "secret-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini", "timeout_seconds": 60})
            summary = provider.get_config_summary()
            assert summary["type"] == "openai"
            assert summary["model"] == "gpt-4o-mini"
            assert summary["timeout_seconds"] == 60
            assert "api_key" not in summary
            assert "secret-key" not in str(summary)

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check returns True on success."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            # Mock the client's get method
            mock_response = MagicMock()
            mock_response.status_code = 200
            provider.client.get = AsyncMock(return_value=mock_response)

            result = await provider.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check returns False on failure."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            provider.client.get = AsyncMock(side_effect=Exception("Connection failed"))

            result = await provider.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message send."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            
            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "chatcmpl-123",
                "model": "gpt-4o-mini",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?",
                    },
                    "finish_reason": "stop",
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            }
            provider.client.post = AsyncMock(return_value=mock_response)

            messages = [Message(role="user", content="Hello")]
            response = await provider.send_message(messages)

            assert response.content == "Hello! How can I help you?"
            assert len(response.tool_calls) == 0
            assert response.metadata["model"] == "gpt-4o-mini"
            assert response.metadata["usage"]["total_tokens"] == 15
            assert response.metadata["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_send_message_with_tools(self):
        """Test message send with tool calls."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o"})
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "chatcmpl-123",
                "model": "gpt-4o",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "San Francisco"}',
                            },
                        }],
                    },
                    "finish_reason": "tool_calls",
                }],
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
            }
            provider.client.post = AsyncMock(return_value=mock_response)

            messages = [Message(role="user", content="What's the weather in SF?")]
            tools = [{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for a location",
                    "parameters": {"type": "object", "properties": {"location": {"type": "string"}}},
                },
            }]
            response = await provider.send_message(messages, tools=tools)

            assert response.content == ""
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0].name == "get_weather"
            assert response.tool_calls[0].arguments == {"location": "San Francisco"}

    @pytest.mark.asyncio
    async def test_send_message_auth_error(self):
        """Test authentication error handling."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            
            mock_response = MagicMock()
            mock_response.status_code = 401
            import httpx
            provider.client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=mock_response
            ))

            messages = [Message(role="user", content="Hello")]
            with pytest.raises(RuntimeError, match="authentication failed"):
                await provider.send_message(messages)

    @pytest.mark.asyncio
    async def test_send_message_rate_limit(self):
        """Test rate limit error handling."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            
            mock_response = MagicMock()
            mock_response.status_code = 429
            import httpx
            provider.client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Rate limited", request=MagicMock(), response=mock_response
            ))

            messages = [Message(role="user", content="Hello")]
            with pytest.raises(RuntimeError, match="rate limit exceeded"):
                await provider.send_message(messages)

    @pytest.mark.asyncio
    async def test_send_message_server_error(self):
        """Test server error handling."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            
            mock_response = MagicMock()
            mock_response.status_code = 500
            import httpx
            provider.client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Server error", request=MagicMock(), response=mock_response
            ))

            messages = [Message(role="user", content="Hello")]
            with pytest.raises(RuntimeError, match="server error"):
                await provider.send_message(messages)

    @pytest.mark.asyncio
    async def test_send_message_network_error(self):
        """Test network error handling."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            import httpx
            provider.client.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))

            messages = [Message(role="user", content="Hello")]
            with pytest.raises(RuntimeError, match="request failed"):
                await provider.send_message(messages)

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test closing the HTTP client."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            provider.client.aclose = AsyncMock()
            await provider.close()
            provider.client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            provider = OpenAIProvider({"model": "gpt-4o-mini"})
            provider.client.aclose = AsyncMock()
            
            async with provider as p:
                assert p is provider
            
            provider.client.aclose.assert_called_once()
