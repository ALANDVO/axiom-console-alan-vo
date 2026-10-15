from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    role: str  # system, user, assistant
    content: str


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    result: Any
    error: Optional[str] = None


class ProviderResponse(BaseModel):
    content: str
    tool_calls: List[ToolCall] = []
    metadata: Dict[str, Any] = {}


class ProviderCapabilities(BaseModel):
    supports_tools: bool = False
    supports_streaming: bool = False
    supports_system_prompt: bool = True
    max_tokens: Optional[int] = None


class BaseProvider(ABC):
    """Abstract base class for all model providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model")
        self.timeout = config.get("timeout_seconds", 30)

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Unique identifier for this provider type."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Return the capabilities of this provider."""
        pass

    @abstractmethod
    async def send_message(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Send a message to the model and get a response."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        pass

    def get_config_summary(self) -> Dict[str, Any]:
        """Return a summary of the provider config (without secrets)."""
        return {
            "type": self.provider_type,
            "model": self.model,
            "timeout_seconds": self.timeout,
        }