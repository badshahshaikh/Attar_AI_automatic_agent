"""
providers/factory.py
--------------------
LLM Provider Factory for creating provider instances.
"""

from attar_ai.app.core.config import settings
from attar_ai.app.core.exceptions import ConfigurationError
from attar_ai.app.providers.base import LLMProvider
from attar_ai.app.providers.cloudflare_provider import CloudflareProvider
from attar_ai.app.providers.groq_provider import GroqProvider
from attar_ai.app.providers.openai_provider import OpenAIProvider


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    _provider: LLMProvider | None = None

    @classmethod
    def create_provider(cls) -> LLMProvider:
        """Create and return the configured LLM provider."""
        if cls._provider is not None:
            return cls._provider

        provider_type = settings.llm_provider.lower()

        if provider_type == "openai":
            cls._provider = OpenAIProvider()
        elif provider_type == "cloudflare":
            cls._provider = CloudflareProvider()
        elif provider_type == "groq":
            cls._provider = GroqProvider()
        else:
            raise ConfigurationError(
                f"Invalid LLM_PROVIDER='{provider_type}'. "
                "Must be one of: 'openai', 'cloudflare', 'groq'."
            )

        return cls._provider

    @classmethod
    def get_provider(cls) -> LLMProvider:
        """Get the cached provider instance, creating it if necessary."""
        if cls._provider is None:
            return cls.create_provider()
        return cls._provider

    @classmethod
    def reset_provider(cls) -> None:
        """Reset the cached provider (useful for testing)."""
        cls._provider = None


def get_provider() -> LLMProvider:
    """Convenience function to get the active provider."""
    return LLMProviderFactory.get_provider()