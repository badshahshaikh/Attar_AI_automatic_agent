"""
providers/cloudflare_provider.py
--------------------------------
Cloudflare Workers AI provider implementation.
"""

from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from attar_ai.app.core.config import settings
from attar_ai.app.providers.base import LLMProvider


class CloudflareProvider(LLMProvider):
    """Cloudflare Workers AI provider (OpenAI-compatible endpoint)."""

    def __init__(self):
        super().__init__(model=settings.cloudflare_model, timeout=settings.cloudflare_timeout)
        self.client = OpenAI(
            api_key=settings.cloudflare_api_token,
            base_url=(
                f"https://api.cloudflare.com/client/v4/accounts/"
                f"{settings.cloudflare_account_id}/ai/v1"
            ),
            timeout=settings.cloudflare_timeout,
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
            self._handle_error(exc, "cloudflare")

    def supports_parallel_tool_calls(self) -> bool:
        return True