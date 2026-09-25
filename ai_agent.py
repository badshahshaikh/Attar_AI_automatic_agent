"""
ai_agent.py
-----------
Manages the conversation with OpenAI. Handles:
  - Loading the system prompt (re-read on every request — edits take effect immediately)
  - Running the agentic tool-calling loop
  - Calling the live Google Sheets inventory tool
  - Basic observability: duration, tool usage, errors
  - Returning structured output for easy inspection in /docs
"""

import json
import logging
import os
import time
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv

# Google Sheets lookup is the live inventory source
from sheets_lookup import lookup_product, LOOKUP_TOOL_SCHEMA

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _load_system_prompt() -> str:
    """Read system_prompt.txt fresh each request so manual edits take effect immediately."""
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Agentic loop
# ---------------------------------------------------------------------------

def chat(
    message: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    Send a customer message to the AI agent and return a structured response.

    Parameters
    ----------
    message : str
        The latest customer message (English or Hinglish).
    history : list[dict] | None
        Previous turns as [{"role": "user"|"assistant", "content": "..."}].
        Pass [] to start a fresh conversation.

    Returns
    -------
    dict with keys:
        customer_message  – the original input
        reply             – the AI's final text reply
        tool_calls_made   – list of inventory lookups made (name + args)
        tool_results      – the actual sheet data returned for each lookup
        updated_history   – full conversation to pass back on the next call
        observability     – {duration_ms, openai_called, tool_called,
                             lookup_args, error}
    """

    t_start = time.monotonic()

    obs: dict[str, Any] = {
        "duration_ms": 0,
        "openai_called": False,
        "tool_called": False,
        "lookup_args": [],
        "error": None,
    }

    history = history or []
    system_prompt = _load_system_prompt()

    # Build messages list
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    tool_calls_made: list[dict] = []
    tool_results: list[dict] = []
    final_reply = ""

    try:
        # ---- Agentic loop: iterate until the model stops calling tools ------
        MAX_ITERATIONS = 5
        for _ in range(MAX_ITERATIONS):
            obs["openai_called"] = True
            response = _client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=[LOOKUP_TOOL_SCHEMA],
                tool_choice="auto",
            )

            assistant_message = response.choices[0].message
            messages.append(assistant_message)

            # No tool calls → final reply
            if not assistant_message.tool_calls:
                final_reply = assistant_message.content or ""
                logger.info(
                    "chat complete | model=%s | tool_calls=%d | msg_preview=%.80s",
                    OPENAI_MODEL,
                    len(tool_calls_made),
                    final_reply,
                )
                break

            # ---- Process each tool call ------------------------------------
            for tc in assistant_message.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                # Record lookup for observability + response
                obs["tool_called"] = True
                obs["lookup_args"].append(fn_args)
                tool_calls_made.append({"tool": fn_name, "arguments": fn_args})

                logger.info(
                    "tool_call | fn=%s | args=%s",
                    fn_name,
                    json.dumps(fn_args, ensure_ascii=False),
                )

                # Execute the tool
                if fn_name == "lookup_product":
                    result_json = lookup_product(
                        product_name=fn_args.get("product_name", ""),
                        size=fn_args.get("size"),
                    )
                else:
                    result_json = json.dumps({"error": f"Unknown tool: {fn_name}"})

                parsed_result = json.loads(result_json)
                tool_results.append({"tool": fn_name, "result": parsed_result})

                logger.info(
                    "tool_result | fn=%s | rows_returned=%s",
                    fn_name,
                    len(parsed_result) if isinstance(parsed_result, list) else "non-list",
                )

                # Feed result back to the model
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_json,
                    }
                )
        else:
            final_reply = "Sorry, I couldn't process your request. Please try again."
            logger.warning("chat loop exhausted MAX_ITERATIONS without a final reply")

    except Exception as exc:
        obs["error"] = str(exc)
        logger.exception("Unexpected error in chat()")
        # Surface a safe message — never expose internal details to the customer
        final_reply = "Sorry, something went wrong. Please try again in a moment."

    # ---- Observability: record total wall-clock time -----------------------
    obs["duration_ms"] = round((time.monotonic() - t_start) * 1000)

    logger.info(
        "request_summary | duration_ms=%d | openai_called=%s | tool_called=%s | error=%s",
        obs["duration_ms"],
        obs["openai_called"],
        obs["tool_called"],
        obs["error"],
    )

    # ---- Build updated history (strip system message) ----------------------
    raw_history = [m for m in messages if not isinstance(m, dict) or m.get("role") != "system"]

    serialisable_history: list[dict] = []
    for m in raw_history:
        if isinstance(m, dict):
            serialisable_history.append(m)
        else:
            # OpenAI ChatCompletionMessage object
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

    return {
        "customer_message": message,
        "reply": final_reply,
        "tool_calls_made": tool_calls_made,
        "tool_results": tool_results,
        "updated_history": serialisable_history,
        "observability": obs,
    }
