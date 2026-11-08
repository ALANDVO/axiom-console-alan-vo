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


class OllamaProvider(BaseProvider):
    """Ollama local API provider adapter."""

    BASE_URL = "http://localhost:11434"
    CHAT_ENDPOINT = "/api/chat"
    GENERATE_ENDPOINT = "/api/generate"
    TAGS_ENDPOINT = "/api/tags"

    MODEL_CAPABILITIES = {
        "llama3.1": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=8192,
        ),
        "llama3.2": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=8192,
        ),
        "mistral": ProviderCapabilities(
            supports_tools=False,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=4096,
        ),
        "codellama": ProviderCapabilities(
            supports_tools=False,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=4096,
        ),
        "gemma2": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=8192,
        ),
        "qwen2.5": ProviderCapabilities(
            supports_tools=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=8192,
        ),
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("LLM_API_KEY")
        self.base_url = config.get("base_url", self.BASE_URL)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
        )

    @property
    def provider_type(self) -> str:
        return "ollama"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.MODEL_CAPABILITIES.get(self.model, ProviderCapabilities(
            supports_tools=False,
            supports_streaming=True,
            supports_system_prompt=True,
            max_tokens=None,
        ))

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(self.TAGS_ENDPOINT)
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
        payload = self._build_payload(messages, tools, system_prompt, **kwargs)

        try:
            response = await self.client.post(
                self.CHAT_ENDPOINT,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)
        except httpx.HTTPStatusError as e:
            raise self._handle_error(e)
        except httpx.RequestError as e:
            raise RuntimeError(f"Ollama request failed: {type(e).__name__}") from e

    def _build_payload(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]],
        system_prompt: Optional[str],
        **kwargs,
    ) -> Dict[str, Any]:
        ollama_messages = []

        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            ollama_messages.append({"role": msg.role, "content": msg.content})

        payload: Dict[str, Any] = {
            "model": self.model or "llama3.1",
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens") or self.capabilities.max_tokens or 4096,
            },
        }

        if tools and self.capabilities.supports_tools:
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
                payload["tools"] = [{"type": "function", "function": f} for f in function_declarations]

        return payload

    def _parse_response(self, data: Dict[str, Any]) -> ProviderResponse:
        message = data.get("message", {})
        content = message.get("content", "") or ""
        tool_calls = []

        if "tool_calls" in message:
            for tc in message["tool_calls"]:
                func = tc.get("function", {})
                tool_calls.append(ToolCall(
                    id=tc.get("id", func.get("name", "unknown")),
                    name=func.get("name", "unknown"),
                    arguments=func.get("arguments", {}),
                ))

        return ProviderResponse(
            content=content,
            tool_calls=tool_calls,
            metadata={
                "model": data.get("model"),
                "done": data.get("done"),
                "total_duration": data.get("total_duration"),
                "eval_count": data.get("eval_count"),
            },
        )

    def _handle_error(self, error: httpx.HTTPStatusError) -> Exception:
        status = error.response.status_code

        if status == 401:
            return RuntimeError("Ollama authentication failed: invalid API key")
        elif status == 404:
            return RuntimeError(f"Ollama model not found: {self.model}")
        elif status >= 500:
            return RuntimeError("Ollama server error")
        else:
            return RuntimeError(f"Ollama API error: {status}")

    def get_config_summary(self) -> Dict[str, Any]:
        summary = super().get_config_summary()
        summary["base_url"] = self.base_url
        return summary

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
