"""
services/conversation_service.py
---------------------------------
Conversation history management service.
"""

import logging
from typing import Any

from attar_ai.app.core.logging import get_logger

logger = get_logger(__name__)


class ConversationService:
    """Manage conversation history and serialization."""

    def __init__(self):
        pass

    def trim_history(self, history: list[dict[str, Any]], max_turns: int) -> list[dict[str, Any]]:
        """Trim conversation history to the maximum number of turns."""
        if len(history) > max_turns:
            logger.info("trimming history from %d to %d entries", len(history), max_turns)
            return history[-max_turns:]
        return history

    def serialize_history(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Convert message objects to serializable dictionaries.

        Strips system messages and ensures all entries are plain dicts.
        """
        # Remove system messages
        raw_history = [m for m in messages if not isinstance(m, dict) or m.get("role") != "system"]

        serialisable_history: list[dict] = []
        for m in raw_history:
            if isinstance(m, dict):
                serialisable_history.append(m)
            else:
                # Handle OpenAI ChatCompletionMessage objects
                entry: dict = {"role": m.role, "content": m.content or ""}
                if hasattr(m, "tool_calls") and m.tool_calls:
                    entry["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in m.tool_calls
                    ]
                serialisable_history.append(entry)

        return serialisable_history

    def validate_history(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate and clean conversation history."""
        if not isinstance(history, list):
            return []
        validated = []
        for entry in history:
            if not isinstance(entry, dict):
                continue
            role = entry.get("role")
            content = entry.get("content")
            if role not in ("user", "assistant", "tool"):
                continue
            if content is None:
                content = ""
            validated.append({"role": role, "content": content})
            if "tool_calls" in entry:
                validated[-1]["tool_calls"] = entry["tool_calls"]
            if "tool_call_id" in entry:
                validated[-1]["tool_call_id"] = entry["tool_call_id"]
        return validated


# Global service instance
conversation_service = ConversationService()