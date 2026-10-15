import json
import random
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.services.providers.base import (
    BaseProvider,
    Message,
    ProviderCapabilities,
    ProviderResponse,
    ToolCall,
    ToolResult,
)


class MockProvider(BaseProvider):
    """Deterministic mock provider for testing without API keys."""

    @property
    def provider_type(self) -> str:
        return "mock"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_tools=True,
            supports_streaming=False,
            supports_system_prompt=True,
            max_tokens=4096,
        )

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.seed = config.get("seed", 42)
        self._rng = random.Random(self.seed)
        self.fail_rate = config.get("fail_rate", 0.0)
        self.latency_ms = config.get("latency_ms", 0)

    async def health_check(self) -> bool:
        return True

    async def send_message(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate a deterministic mock response based on the last user message."""
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.role == "user":
                last_user_msg = msg.content
                break

        # Deterministic response based on message content hash
        msg_hash = hash(last_user_msg + str(self.seed)) % 10000

        # Simulate tool calls if tools are provided and message suggests tool use
        tool_calls = []
        if tools and self._should_call_tool(last_user_msg, msg_hash):
            tool = self._rng.choice(tools)
            tool_calls.append(
                ToolCall(
                    id=f"call_{msg_hash:04d}",
                    name=tool["function"]["name"],
                    arguments=self._generate_mock_args(tool["function"]["name"]),
                )
            )

        # Generate response content
        content = self._generate_response(last_user_msg, msg_hash, tool_calls)

        return ProviderResponse(
            content=content,
            tool_calls=tool_calls,
            metadata={"mock": True, "seed": self.seed, "msg_hash": msg_hash},
        )

    def _should_call_tool(self, message: str, msg_hash: int) -> bool:
        """Determine if a tool should be called based on message content."""
        tool_keywords = ["read", "write", "delete", "export", "search", "get", "list"]
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in tool_keywords):
            return msg_hash % 3 == 0  # ~33% chance
        return False

    def _generate_mock_args(self, tool_name: str) -> Dict[str, Any]:
        """Generate mock arguments for a tool."""
        args_map = {
            "read_record": {"record_id": f"rec_{self._rng.randint(1, 1000)}"},
            "write_record": {"record_id": f"rec_{self._rng.randint(1, 1000)}", "data": {"mock": True}},
            "delete_record": {"record_id": f"rec_{self._rng.randint(1, 1000)}"},
            "export_data": {"format": "json", "scope": "all"},
            "purge_archive": {"confirm": True},
        }
        return args_map.get(tool_name, {"param": "value"})

    def _generate_response(
        self, message: str, msg_hash: int, tool_calls: List[ToolCall]
    ) -> str:
        """Generate a mock response content."""
        if tool_calls:
            return f"I'll help you with that. Let me call the {tool_calls[0].name} tool."

        # Deterministic responses based on message type
        responses = [
            "I understand your request. Let me assist you with that.",
            "Based on the information provided, I can help you with this task.",
            "I'll process your request and provide the appropriate response.",
            "This is a mock response from the deterministic provider.",
            "I've analyzed your input and here is my response.",
        ]
        return responses[msg_hash % len(responses)]


class MockProviderWithFixtures(MockProvider):
    """Mock provider that uses fixture data for more realistic responses."""

    def __init__(self, config: Dict[str, Any], fixture: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.fixture = fixture or {}
        self.tools = self.fixture.get("tools", [])
        self.permissions = self.fixture.get("permissions", [])
        self.users = self.fixture.get("users", [])
        self.policies = self.fixture.get("policies", {})
        self.governance = self.fixture.get("governance", {})

    def _should_call_tool(self, message: str, msg_hash: int) -> bool:
        # More likely to call tools if fixture has tools defined
        if self.tools:
            return msg_hash % 2 == 0  # 50% chance
        return super()._should_call_tool(message, msg_hash)

    def _generate_mock_args(self, tool_name: str) -> Dict[str, Any]:
        # Use fixture tool definitions if available
        tool_def = next((t for t in self.tools if t.get("tool_id") == tool_name), None)
        if tool_def:
            return {"tool_id": tool_name, "fixture_defined": True}
        return super()._generate_mock_args(tool_name)

    def check_permission(self, user_id: str, tool_id: str) -> bool:
        """Check if a user has permission to use a tool based on fixture."""
        user = next((u for u in self.users if u.get("user_id") == user_id), None)
        if not user:
            return False
        user_roles = user.get("roles", [])
        for perm in self.permissions:
            if perm.get("role") in user_roles and tool_id in perm.get("tools", []):
                return True
        return False