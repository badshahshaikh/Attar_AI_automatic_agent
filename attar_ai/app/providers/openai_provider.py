"""
providers/openai_provider.py
----------------------------
OpenAI LLM provider implementation.
"""

from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from attar_ai.app.core.config import settings
from attar_ai.app.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self):
        super().__init__(model=settings.openai_model, timeout=settings.openai_timeout)
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout,
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
            self._handle_error(exc, "openai")

    def supports_parallel_tool_calls(self) -> bool:
        return True