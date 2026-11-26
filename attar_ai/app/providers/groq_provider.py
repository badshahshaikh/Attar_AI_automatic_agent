"""
providers/groq_provider.py
--------------------------
Groq LLM provider implementation.
"""

from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from attar_ai.app.core.config import settings
from attar_ai.app.providers.base import LLMProvider


class GroqProvider(LLMProvider):
    """Groq API provider (OpenAI-compatible endpoint)."""

    def __init__(self):
        super().__init__(model=settings.groq_model, timeout=settings.groq_timeout)
        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            timeout=settings.groq_timeout,
        )

    def create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = "auto",
        temperature: float = 0.2,
    ) -> ChatCompletion:
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice

            return self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            self._handle_error(exc, "groq")

    def supports_parallel_tool_calls(self) -> bool:
        # Groq does NOT support parallel tool calls
        return False