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


class OpenAIProvider(BaseProvider):
    """OpenAI API provider adapter."""

    # API endpoints
    BASE_URL = "https://api.openai.com/v1"
    CHAT_COMPLETIONS_ENDPOINT = "/chat/completions"

    # Model capabilities mapping
    MODEL_CAPABILITIES = {
        "gpt-4o": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=4096,
        ),
        "gpt-4o-mini": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=4096,
        ),
        "gpt-4-turbo": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=4096,
        ),
        "gpt-3.5-turbo": ProviderCapabilities(
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
            raise ValueError("OpenAI API key required: set LLM_API_KEY environment variable or pass api_key in config")

        self.base_url = config.get("base_url", self.BASE_URL)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

    @property
    def provider_type(self) -> str:
        return "openai"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.MODEL_CAPABILITIES.get(self.model, ProviderCapabilities(
            supports_tools=False,
            supports_streaming=False,
            supports_system_prompt=True,
            max_tokens=None,
        ))

    async def health_check(self) -> bool:
        """Check if the OpenAI API is reachable."""
        try:
            response = await self.client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    async def send_message(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Send a message to OpenAI Chat Completions API."""
        # Build the request payload
        payload = self._build_payload(messages, tools, system_prompt, **kwargs)

        try:
            response = await self.client.post(
                self.CHAT_COMPLETIONS_ENDPOINT,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)
        except httpx.HTTPStatusError as e:
            raise self._handle_error(e)
        except httpx.RequestError as e:
            raise RuntimeError(f"OpenAI request failed: {type(e).__name__}") from e

    def _build_payload(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]],
        system_prompt: Optional[str],
        **kwargs,
    ) -> Dict[str, Any]:
        """Build the OpenAI API request payload."""
        # Convert messages to OpenAI format
        openai_messages = []

        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            openai_messages.append({"role": msg.role, "content": msg.content})

        payload: Dict[str, Any] = {
            "model": self.model or "gpt-4o-mini",
            "messages": openai_messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens") or self.capabilities.max_tokens,
        }

        if tools and self.capabilities.supports_tools:
            payload["tools"] = tools
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")

        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in payload and key not in ("temperature", "max_tokens", "tool_choice"):
                payload[key] = value

        return payload

    def _parse_response(self, data: Dict[str, Any]) -> ProviderResponse:
        """Parse OpenAI API response into ProviderResponse."""
        choice = data["choices"][0]
        message = choice.get("message", {})

        content = message.get("content", "") or ""
        tool_calls = []

        if "tool_calls" in message:
            for tc in message["tool_calls"]:
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=json.loads(tc["function"]["arguments"]),
                ))

        return ProviderResponse(
            content=content,
            tool_calls=tool_calls,
            metadata={
                "model": data.get("model"),
                "usage": data.get("usage"),
                "finish_reason": choice.get("finish_reason"),
            },
        )

    def _handle_error(self, error: httpx.HTTPStatusError) -> Exception:
        """Handle HTTP errors with redacted messages."""
        status = error.response.status_code

        # Redact sensitive information from error messages
        if status == 401:
            return RuntimeError("OpenAI authentication failed: invalid API key")
        elif status == 429:
            return RuntimeError("OpenAI rate limit exceeded")
        elif status >= 500:
            return RuntimeError("OpenAI server error")
        else:
            # Don't expose response body which may contain sensitive info
            return RuntimeError(f"OpenAI API error: {status}")

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
