"""
schemas/chat.py
---------------
Chat request/response schemas.
"""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""

    message: str = Field(
        ...,
        description="The customer's message (English or Hinglish).",
        examples=["Do you have Rose Attar in 6ml?"],
    )
    history: list[dict[str, Any]] = Field(
        default=[],
        description=(
            "Conversation history from a previous /chat call. "
            "Pass the `updated_history` from the last response to support follow-up questions. "
            "Leave empty [] to start a new conversation."
        ),
    )


class ObservabilityInfo(BaseModel):
    """Observability information for a chat request."""

    duration_ms: int = Field(description="Total wall-clock time for this request in milliseconds.")
    provider: str = Field(description="LLM provider used.")
    model: str = Field(description="Model name used.")
    openai_called: bool = Field(description="Whether the LLM API was called.")
    tool_called: bool = Field(description="Whether any agent tool was called.")
    lookup_args: list[dict[str, Any]] = Field(description="Arguments passed to each tool call.")
    error: str | None = Field(default=None, description="Error message if something went wrong.")
    tool_rounds: int = Field(default=0, description="Number of tool calling rounds.")
    token_usage: dict[str, int | None] | None = Field(default=None, description="Token usage if available.")
    empty_reply_retries: int = Field(default=0, description="Number of empty reply retries.")
    final_finish_reason: str | None = Field(default=None, description="Finish reason from the final response.")
    empty_final_response: bool = Field(default=False, description="Whether the final response was empty.")


class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""

    customer_message: str = Field(description="The original customer message.")
    reply: str = Field(description="The AI agent's final reply to the customer.")
    tool_calls_made: list[dict[str, Any]] = Field(
        description="List of tool calls the AI requested (tool name + arguments)."
    )
    tool_results: list[dict[str, Any]] = Field(
        description="The actual data returned for each tool call."
    )
    updated_history: list[dict[str, Any]] = Field(
        description="Full conversation history. Pass this back in the next request for follow-up questions."
    )
    observability: ObservabilityInfo = Field(
        description="Lightweight metrics for this request: timing, tool usage, and errors."
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="ok")
    message: str = Field(default="MS Fragrances AI Agent is running.")