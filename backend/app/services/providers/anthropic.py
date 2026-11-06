import os
import json
from typing import Any, Dict, List, Optional
import httpx

from app.services.providers.base import (
    BaseProvider,
    Message,
    ProviderCapabilities,
    ProviderResponse,
    ToolCall,
    ToolResult,
)


class AnthropicProvider(BaseProvider):
    """Anthropic API provider adapter."""

    # API endpoints
    BASE_URL = "https://api.anthropic.com/v1"
    MESSAGES_ENDPOINT = "/messages"

    # Model capabilities mapping
    MODEL_CAPABILITIES = {
        "claude-3-5-sonnet-20241022": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=8192,
        ),
        "claude-3-5-haiku-20241022": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=8192,
        ),
        "claude-3-opus-20240229": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=4096,
        ),
        "claude-3-sonnet-20240229": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=4096,
        ),
        "claude-3-haiku-20240307": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=4096,
        ),
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # API key from environment (server-side only)
        self.api_key = config.get("api_key") or os.environ.get("LLM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required: set LLM_API_KEY environment variable or pass api_key in config"
            )

        self.base_url = config.get("base_url", self.BASE_URL)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )

    @property
    def provider_type(self) -> str:
        return "anthropic"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.MODEL_CAPABILITIES.get(self.model, ProviderCapabilities(
            supports_tools=False,
            supports_streaming=False,
            supports_system_prompt=True,
            max_tokens=None,
        ))

    async def health_check(self) -> bool:
        """Check if the Anthropic API is reachable."""
        try:
            # Anthropic doesn't have a simple models endpoint, so we try a minimal request
            response = await self.client.post(
                self.MESSAGES_ENDPOINT,
                json={
                    "model": self.model or "claude-3-5-haiku-20241022",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1,
                },
            )
            # 400 is expected for minimal request, but means API is reachable
            return response.status_code in (200, 400)
        except Exception:
            return False

    async def send_message(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Send a message to Anthropic Messages API."""
        payload = self._build_payload(messages, tools, system_prompt, **kwargs)

        try:
            response = await self.client.post(
                self.MESSAGES_ENDPOINT,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)
        except httpx.HTTPStatusError as e:
            raise self._handle_error(e)
        except httpx.RequestError as e:
            raise RuntimeError(f"Anthropic request failed: {type(e).__name__}") from e

    def _build_payload(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]],
        system_prompt: Optional[str],
        **kwargs,
    ) -> Dict[str, Any]:
        """Build the Anthropic API request payload."""
        # Convert messages to Anthropic format (no system role in messages)
        anthropic_messages = []
        for msg in messages:
            if msg.role == "system":
                # System messages are handled separately in Anthropic
                continue
            anthropic_messages.append({"role": msg.role, "content": msg.content})

        payload: Dict[str, Any] = {
            "model": self.model or "claude-3-5-haiku-20241022",
            "messages": anthropic_messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens") or self.capabilities.max_tokens or 4096,
        }

        if system_prompt:
            payload["system"] = system_prompt

        if tools and self.capabilities.supports_tools:
            payload["tools"] = tools
            payload["tool_choice"] = kwargs.get("tool_choice", {"type": "auto"})

        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in payload and key not in ("temperature", "max_tokens", "tool_choice", "system"):
                payload[key] = value

        return payload

    def _parse_response(self, data: Dict[str, Any]) -> ProviderResponse:
        """Parse Anthropic API response into ProviderResponse."""
        content_blocks = data.get("content", [])
        content = ""
        tool_calls = []

        for block in content_blocks:
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(ToolCall(
                    id=block["id"],
                    name=block["name"],
                    arguments=block["input"],
                ))

        return ProviderResponse(
            content=content,
            tool_calls=tool_calls,
            metadata={
                "model": data.get("model"),
                "usage": data.get("usage"),
                "stop_reason": data.get("stop_reason"),
            },
        )

    def _handle_error(self, error: httpx.HTTPStatusError) -> Exception:
        """Handle HTTP errors with redacted messages."""
        status = error.response.status_code

        # Redact sensitive information from error messages
        if status == 401:
            return RuntimeError("Anthropic authentication failed: invalid API key")
        elif status == 429:
            return RuntimeError("Anthropic rate limit exceeded")
        elif status >= 500:
            return RuntimeError("Anthropic server error")
        else:
            # Don't expose response body which may contain sensitive info
            return RuntimeError(f"Anthropic API error: {status}")

    def get_config_summary(self) -> Dict[str, Any]:
        """Return config summary without secrets."""
        summary = super().get_config_summary()
        summary["base_url"] = self.base_url
        return summary

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
