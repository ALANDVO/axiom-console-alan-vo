from typing import Any, Dict, Optional, Type

from app.services.providers.base import BaseProvider
from app.services.providers.mock import MockProvider, MockProviderWithFixtures


class ProviderRegistry:
    """Registry for provider classes."""

    _providers: Dict[str, Type[BaseProvider]] = {
        "mock": MockProvider,
        "mock_with_fixtures": MockProviderWithFixtures,
    }

    @classmethod
    def register(cls, name: str, provider_class: Type[BaseProvider]) -> None:
        """Register a new provider type."""
        cls._providers[name] = provider_class

    @classmethod
    def get_provider_class(cls, name: str) -> Optional[Type[BaseProvider]]:
        """Get a provider class by name."""
        return cls._providers.get(name)

    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any], fixture: Optional[Dict[str, Any]] = None) -> BaseProvider:
        """Create a provider instance."""
        provider_class = cls.get_provider_class(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider_type}")

        if provider_class == MockProviderWithFixtures:
            return provider_class(config, fixture)
        return provider_class(config)

    @classmethod
    def list_providers(cls) -> Dict[str, Dict[str, Any]]:
        """List all registered providers with their capabilities."""
        result = {}
        for name, provider_class in cls._providers.items():
            # Create a dummy instance to get capabilities
            try:
                instance = provider_class({"model": "test"})
                result[name] = instance.capabilities.model_dump()
            except Exception:
                result[name] = {"error": "Could not instantiate"}
        return result


# Convenience function
def create_provider(provider_type: str, config: Dict[str, Any], fixture: Optional[Dict[str, Any]] = None) -> BaseProvider:
    return ProviderRegistry.create_provider(provider_type, config, fixture)