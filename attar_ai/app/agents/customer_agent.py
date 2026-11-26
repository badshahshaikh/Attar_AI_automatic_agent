"""
agents/customer_agent.py
------------------------
Customer agent that manages the LLM tool-calling loop.
"""

import json
import time
from typing import Any

from openai.types.chat import ChatCompletionMessageParam

from attar_ai.app.agents.agent_state import AgentState
from attar_ai.app.agents.tool_registry import ToolRegistry
from attar_ai.app.core.config import settings
from attar_ai.app.core.exceptions import ProviderError, ValidationError
from attar_ai.app.core.logging import get_logger
from attar_ai.app.providers.factory import get_provider
from attar_ai.app.schemas.chat import ObservabilityInfo

logger = get_logger(__name__)


class CustomerAgent:
    """Manages the LLM tool-calling loop and generates customer responses."""

    MAX_ITERATIONS = 10
    MAX_EMPTY_REPLY_RETRIES = 2

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.provider = get_provider()
        self.llm_provider_name = settings.llm_provider
        self.model = settings.get_active_model()

    def load_system_prompt(self) -> str:
        """Load the system prompt from file."""
        prompt_path = settings.system_prompt_path
        if not prompt_path.startswith("/"):
            # Resolve relative to project root
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            prompt_path = os.path.join(project_root, prompt_path)

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def run(
        self,
        message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> tuple[str, list[dict], list[dict], list[ChatCompletionMessageParam], ObservabilityInfo]:
        """
        Run the agent for a single customer message.

        Returns:
            tuple: (final_reply, tool_calls_made, tool_results, updated_history, observability)
        """
        t_start = time.monotonic()

        obs = ObservabilityInfo(
            duration_ms=0,
            provider=self.llm_provider_name,
            model=self.model,
            openai_called=False,
            tool_called=False,
            lookup_args=[],
            error=None,
            tool_rounds=0,
            token_usage=None,
            empty_reply_retries=0,
            final_finish_reason=None,
            empty_final_response=False,
        )

        # Gracefully reject empty / non-string input
        if not isinstance(message, str) or not message.strip():
            obs.error = "empty_message"
            obs.duration_ms = round((time.monotonic() - t_start) * 1000)
            logger.warning("chat() rejected an empty or invalid message")
            return (
                "Please type a message so I can help you.",
                [],
                [],
                history or [],
                obs,
            )

        history = history or []

        # Cap conversation history
        if len(history) > settings.max_history_turns:
            logger.info(
                "trimming history from %d to %d entries", len(history), settings.max_history_turns
            )
            history = history[-settings.max_history_turns:]

        system_prompt = self.load_system_prompt()

        # Build messages list
        messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        state = AgentState()
        state.messages = messages

        try:
            # Agentic loop
            for _ in range(self.MAX_ITERATIONS):
                obs.openai_called = True

                create_kwargs = {
                    "messages": state.messages,
                    "temperature": 0.2,
                }

                if state.force_answer:
                    create_kwargs["tool_choice"] = "none"
                    if not state.force_answer_injected:
                        state.messages.append({
                            "role": "user",
                            "content": (
                                "You already have the inventory information above. "
                                "Now provide your final answer to the customer. "
                                "Do not call any more tools."
                            ),
                        })
                        state.force_answer_injected = True
                        create_kwargs["messages"] = state.messages
                else:
                    # Get and validate tool schemas before sending to provider
                    tool_schemas = self.tool_registry.get_schemas()
                    self._validate_tool_schemas(tool_schemas)
                    create_kwargs["tools"] = tool_schemas
                    create_kwargs["tool_choice"] = "auto"

                response = self.provider.create_chat_completion(**create_kwargs)

                assistant_message = response.choices[0].message
                assistant_entry: ChatCompletionMessageParam = {
                    "role": "assistant",
                    "content": assistant_message.content or "",
                }
                if getattr(assistant_message, "tool_calls", None):
                    # Validate assistant tool calls have valid function names
                    self._validate_assistant_tool_calls(assistant_message.tool_calls)
                    assistant_entry["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ]
                state.messages.append(assistant_entry)

                # No tool calls → final reply
                if not assistant_message.tool_calls:
                    content = assistant_message.content or ""
                    finish_reason = getattr(response.choices[0], "finish_reason", None)
                    obs.final_finish_reason = finish_reason

                    # Handle empty reply with tool results
                    if not content.strip() and state.tool_results:
                        if obs.empty_reply_retries < self.MAX_EMPTY_REPLY_RETRIES:
                            obs.empty_reply_retries += 1
                            logger.warning(
                                "Empty model reply after %d tool results — retrying (attempt %d)",
                                len(state.tool_results), obs.empty_reply_retries
                            )
                            state.messages.append({
                                "role": "user",
                                "content": (
                                    "You already have inventory information from the lookups above. "
                                    "Please provide a final helpful answer to the customer using that information. "
                                    "Do not call any more tools."
                                ),
                            })
                            continue
                        else:
                            obs.empty_final_response = True
                            final_reply = (
                                "I found the product information but couldn't generate a response. "
                                "Please try asking again."
                            )
                            logger.error(
                                "Empty model reply after %d tool results — giving up after %d retries",
                                len(state.tool_results), obs.empty_reply_retries
                            )
                            break

                    # Empty reply with no tool results
                    if not content.strip():
                        obs.empty_final_response = True
                        final_reply = "I'm sorry, I couldn't generate a response. Please try again."
                        logger.warning("Empty model reply with no tool results — returning fallback")
                        break

                    final_reply = content
                    # Record token usage
                    usage = getattr(response, "usage", None)
                    if usage:
                        obs.token_usage = {
                            "prompt_tokens": getattr(usage, "prompt_tokens", None),
                            "completion_tokens": getattr(usage, "completion_tokens", None),
                            "total_tokens": getattr(usage, "total_tokens", None),
                        }
                    logger.info(
                        "chat complete | provider=%s | model=%s | tool_calls=%d | msg_preview=%.80s",
                        self.llm_provider_name,
                        self.model,
                        len(state.tool_calls_made),
                        final_reply,
                    )
                    break

                # Process tool calls
                tool_calls = assistant_message.tool_calls
                if self.llm_provider_name == "groq":
                    # Groq does NOT support parallel tool calls
                    tool_calls = tool_calls[:1]

                for tc in tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = (
                            json.loads(tc.function.arguments) if tc.function.arguments else {}
                        )
                    except (json.JSONDecodeError, TypeError):
                        fn_args = {}
                    if not isinstance(fn_args, dict):
                        fn_args = {}

                    # Record for observability
                    obs.tool_called = True
                    obs.lookup_args.append(fn_args)

                    # Check for duplicate tool calls
                    if state.is_duplicate_tool_call(fn_name, fn_args):
                        logger.warning("Duplicate tool call detected, forcing final answer: %s::%s", fn_name, fn_args)
                        state.force_answer = True
                        result_json = json.dumps(
                            {"note": "This lookup was already performed. Use the previous result and answer the customer now."},
                            ensure_ascii=False,
                        )
                    else:
                        state.add_tool_call(fn_name, fn_args)
                        try:
                            result_json = self.tool_registry.execute(fn_name, fn_args)
                        except Exception as exc:
                            logger.exception("Tool execution failed | fn=%s", fn_name)
                            result_json = json.dumps(
                                {"error": f"Tool execution failed: {exc}"}, ensure_ascii=False
                            )

                    # Parse result
                    try:
                        parsed_result = json.loads(result_json)
                    except (json.JSONDecodeError, TypeError):
                        parsed_result = {"error": "Tool returned invalid JSON"}

                    state.add_tool_result(fn_name, parsed_result)

                    # Feed result back to model
                    state.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_json,
                    })

                state.increment_tool_round()
                obs.tool_rounds = state.tool_rounds

            else:
                final_reply = "Sorry, I couldn't process your request. Please try again."
                logger.warning("chat loop exhausted MAX_ITERATIONS without a final reply")

        except ProviderError as exc:
            obs.error = exc.message
            logger.exception("Provider error in chat() | provider=%s", self.llm_provider_name)
            final_reply = exc.message
        except Exception as exc:
            obs.error = str(exc)
            logger.exception("Unexpected error in chat() | provider=%s", self.llm_provider_name)
            final_reply = "Sorry, something went wrong. Please try again in a moment."

        # Record duration
        obs.duration_ms = round((time.monotonic() - t_start) * 1000)

        logger.info(
            "request_summary | duration_ms=%d | openai_called=%s | tool_called=%s | error=%s",
            obs.duration_ms,
            obs.openai_called,
            obs.tool_called,
            obs.error,
        )

        # Build serializable history
        serialisable_history = self._serialize_history(state.messages)

        return (
            final_reply,
            state.tool_calls_made,
            state.tool_results,
            serialisable_history,
            obs,
        )

    def _serialize_history(self, messages: list[ChatCompletionMessageParam]) -> list[dict[str, Any]]:
        """Convert messages to serializable format (strip system message)."""
        raw_history = [m for m in messages if not isinstance(m, dict) or m.get("role") != "system"]

        serialisable_history: list[dict] = []
        for m in raw_history:
            if isinstance(m, dict):
                serialisable_history.append(m)
            else:
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

    def _validate_tool_schemas(self, schemas: list[dict[str, Any]]) -> None:
        """Validate tool schemas before sending to provider."""
        for schema in schemas:
            if not isinstance(schema, dict):
                raise ValidationError(f"Tool schema must be a dict, got {type(schema).__name__}", field="schema")
            if schema.get("type") != "function":
                raise ValidationError(f"Tool schema type must be 'function', got {schema.get('type')}", field="type")
            function = schema.get("function")
            if not isinstance(function, dict):
                raise ValidationError(f"Tool schema must have 'function' object", field="function")
            func_name = function.get("name")
            if not func_name or not isinstance(func_name, str) or not func_name.strip():
                raise ValidationError(f"Tool function.name must be a non-empty string, got {repr(func_name)}", field="function.name")

    def _validate_assistant_tool_calls(self, tool_calls: list) -> None:
        """Validate that assistant tool calls have valid function names."""
        for tc in tool_calls:
            if not hasattr(tc, "function"):
                raise ValidationError(f"Tool call missing 'function' attribute", field="function")
            func_name = getattr(tc.function, "name", None)
            if not func_name or not isinstance(func_name, str) or not func_name.strip():
                raise ValidationError(f"Assistant tool call function.name must be a non-empty string, got {repr(func_name)}", field="function.name")