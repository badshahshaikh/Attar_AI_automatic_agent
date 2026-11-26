"""
providers/base.py
-----------------
Base LLM provider interface.
"""

from abc import ABC, abstractmethod
from typing import Any

from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from attar_ai.app.core.exceptions import ProviderError


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str, timeout: float):
        self.model = model
        self.timeout = timeout

    @abstractmethod
    def create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = "auto",
        temperature: float = 0.2,
    ) -> ChatCompletion:
        """Create a chat completion with optional tool calling."""
        pass

    @abstractmethod
    def supports_parallel_tool_calls(self) -> bool:
        """Return whether this provider supports parallel tool calls."""
        pass

    def _handle_error(self, exc: Exception, provider_name: str) -> None:
        """Convert provider errors to standardized exceptions."""
        err_text = str(exc).lower()
        if "429" in err_text or "rate limit" in err_text:
            raise ProviderError(
                "The AI service is temporarily busy. Please try again in a moment.",
                provider=provider_name,
                status_code=429,
            ) from exc
        elif "authentication" in err_text or "api key" in err_text:
            raise ProviderError(
                "The AI service is not configured correctly. Please contact support.",
                provider=provider_name,
                status_code=401,
            ) from exc
        elif "timeout" in err_text or "timed out" in err_text:
            raise ProviderError(
                "The AI service took too long to respond. Please try again.",
                provider=provider_name,
                status_code=504,
            ) from exc
        else:
            raise ProviderError(
                f"AI service error: {exc}",
                provider=provider_name,
                status_code=500,
            ) from exc