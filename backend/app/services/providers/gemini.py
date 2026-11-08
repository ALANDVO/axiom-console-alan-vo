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


class GeminiProvider(BaseProvider):
    """Google Gemini API provider adapter."""

    # API endpoints
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    GENERATE_CONTENT_ENDPOINT = "/models/{model}:generateContent"

    # Model capabilities mapping
    MODEL_CAPABILITIES = {
        "gemini-1.5-pro": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=8192,
        ),
        "gemini-1.5-flash": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=8192,
        ),
        "gemini-1.0-pro": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=2048,
        ),
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # API key from environment (server-side only)
        self.api_key = config.get("api_key") or os.environ.get("LLM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key required: set LLM_API_KEY environment variable or pass api_key in config"
            )

        self.base_url = config.get("base_url", self.BASE_URL)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            params={"key": self.api_key},
        )

    @property
    def provider_type(self) -> str:
        return "gemini"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.MODEL_CAPABILITIES.get(self.model, ProviderCapabilities(
            supports_tools=False,
            supports_streaming=False,
            supports_system_prompt=True,
            max_tokens=None,
        ))

    async def health_check(self) -> bool:
        """Check if the Gemini API is reachable."""
        try:
            # Use a minimal request to check API availability
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
        """Send a message to Gemini API."""
        payload = self._build_payload(messages, tools, system_prompt, **kwargs)
        endpoint = self.GENERATE_CONTENT_ENDPOINT.format(model=self.model or "gemini-1.5-flash")

        try:
            response = await self.client.post(
                endpoint,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)
        except httpx.HTTPStatusError as e:
            raise self._handle_error(e)
        except httpx.RequestError as e:
            raise RuntimeError(f"Gemini request failed: {type(e).__name__}") from e

    def _build_payload(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]],
        system_prompt: Optional[str],
        **kwargs,
    ) -> Dict[str, Any]:
        """Build the Gemini API request payload."""
        # Convert messages to Gemini format
        gemini_messages = []

        if system_prompt:
            gemini_messages.append({
                "role": "user",
                "parts": [{"text": system_prompt}]
            })
            gemini_messages.append({
                "role": "model",
                "parts": [{"text": "Understood. I'll follow these instructions."}]
            })

        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            gemini_messages.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })

        payload: Dict[str, Any] = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens") or self.capabilities.max_tokens or 4096,
            },
        }

        if tools and self.capabilities.supports_tools:
            # Convert OpenAI-style tools to Gemini function declarations
            function_declarations = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    function_declarations.append({
                        "name": func.get("name"),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {}),
                    })
            if function_declarations:
                payload["tools"] = [{"functionDeclarations": function_declarations}]
                payload["toolConfig"] = {"functionCallingConfig": {"mode": kwargs.get("tool_choice", "auto")}}

        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in ("temperature", "max_tokens", "tool_choice", "system"):
                if key in ("top_p", "top_k", "candidate_count"):
                    payload["generationConfig"][key] = value

        return payload

    def _parse_response(self, data: Dict[str, Any]) -> ProviderResponse:
        """Parse Gemini API response into ProviderResponse."""
        candidates = data.get("candidates", [])
        if not candidates:
            return ProviderResponse(content="", metadata={"model": data.get("model")})

        candidate = candidates[0]
        content_parts = candidate.get("content", {}).get("parts", [])

        content = ""
        tool_calls = []

        for part in content_parts:
            if "text" in part:
                content += part["text"]
            elif "functionCall" in part:
                func_call = part["functionCall"]
                tool_calls.append(ToolCall(
                    id=func_call.get("name", "unknown"),
                    name=func_call.get("name", "unknown"),
                    arguments=func_call.get("args", {}),
                ))

        return ProviderResponse(
            content=content,
            tool_calls=tool_calls,
            metadata={
                "model": data.get("model"),
                "usage": data.get("usageMetadata"),
                "finish_reason": candidate.get("finishReason"),
            },
        )

    def _handle_error(self, error: httpx.HTTPStatusError) -> Exception:
        """Handle HTTP errors with redacted messages."""
        status = error.response.status_code

        # Redact sensitive information from error messages
        if status == 401:
            return RuntimeError("Gemini authentication failed: invalid API key")
        elif status == 429:
            return RuntimeError("Gemini rate limit exceeded")
        elif status >= 500:
            return RuntimeError("Gemini server error")
        else:
            # Don't expose response body which may contain sensitive info
            return RuntimeError(f"Gemini API error: {status}")

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
