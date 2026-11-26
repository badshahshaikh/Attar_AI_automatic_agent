"""
agents/agent_state.py
---------------------
State management for agent execution.
"""

from dataclasses import dataclass, field
from typing import Any

from openai.types.chat import ChatCompletionMessageParam


@dataclass
class AgentState:
    """Maintains state during agent execution."""

    messages: list[ChatCompletionMessageParam] = field(default_factory=list)
    tool_calls_made: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    seen_tool_calls: set[str] = field(default_factory=set)
    tool_rounds: int = 0
    force_answer: bool = False
    force_answer_injected: bool = False
    empty_reply_retries: int = 0
    final_finish_reason: str | None = None
    empty_final_response: bool = False
    final_reply: str = ""

    def add_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Record a tool call and return its signature for duplicate detection."""
        import json
        signature = tool_name + "::" + json.dumps(arguments, sort_keys=True, ensure_ascii=False)
        self.seen_tool_calls.add(signature)
        self.tool_calls_made.append({"tool": tool_name, "arguments": arguments})
        return signature

    def is_duplicate_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> bool:
        """Check if a tool call with the same arguments was already made."""
        import json
        signature = tool_name + "::" + json.dumps(arguments, sort_keys=True, ensure_ascii=False)
        return signature in self.seen_tool_calls

    def add_tool_result(self, tool_name: str, result: dict[str, Any]) -> None:
        """Record a tool result."""
        self.tool_results.append({"tool": tool_name, "result": result})

    def increment_tool_round(self) -> None:
        """Increment the tool round counter and force answer after 2 rounds."""
        self.tool_rounds += 1
        if self.tool_rounds >= 2:
            self.force_answer = True

    def reset_for_new_iteration(self) -> None:
        """Reset state for a new agent iteration (if needed)."""
        pass