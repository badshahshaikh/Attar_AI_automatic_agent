"""
ai_agent.py
-----------
Manages the conversation with OpenAI.  Handles:
  - Loading the system prompt
  - Running the agentic loop (message → tool call → result → final reply)
  - Returning structured output for easy inspection in /docs
"""

import json
import os
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv

from product_lookup import lookup_product, LOOKUP_TOOL_SCHEMA

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _load_system_prompt() -> str:
    """Read system_prompt.txt fresh each request so edits take effect immediately."""
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
    Send a customer message to the AI agent and get a structured response.

    Parameters
    ----------
    message : str
        The latest customer message.
    history : list[dict] | None
        Previous conversation turns as [{"role": "user"|"assistant", "content": "..."}].
        Pass None or [] to start a new conversation.

    Returns
    -------
    dict with keys:
        customer_message   – the original input
        reply              – the AI's final text reply
        tool_calls_made    – list of tool calls the AI made (name + args)
        tool_results       – the raw JSON results returned for each tool call
        updated_history    – full conversation history to pass back on the next call
    """

    history = history or []
    system_prompt = _load_system_prompt()

    # Build the messages list for the API call
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    tool_calls_made: list[dict] = []
    tool_results: list[dict] = []

    # ---- Agentic loop: keep going until the model stops calling tools -------
    MAX_ITERATIONS = 5  # safety cap to avoid runaway loops
    for _ in range(MAX_ITERATIONS):
        response = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=[LOOKUP_TOOL_SCHEMA],
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        # Append the assistant's response to the message list
        messages.append(assistant_message)

        # If the model made no tool calls, we have the final reply
        if not assistant_message.tool_calls:
            final_reply = assistant_message.content or ""
            break

        # ---- Process each tool call ----------------------------------------
        for tc in assistant_message.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            # Record what the AI asked for
            tool_calls_made.append({"tool": fn_name, "arguments": fn_args})

            # Execute the tool
            if fn_name == "lookup_product":
                result_json = lookup_product(
                    product_name=fn_args.get("product_name", ""),
                    size=fn_args.get("size"),
                )
            else:
                result_json = json.dumps({"error": f"Unknown tool: {fn_name}"})

            # Record the result
            tool_results.append({"tool": fn_name, "result": json.loads(result_json)})

            # Feed the result back to the model
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_json,
                }
            )
    else:
        # Fallback if the loop exhausts iterations
        final_reply = "Sorry, I couldn't process your request. Please try again."

    # ---- Build updated history (strip system message) ----------------------
    updated_history = [m for m in messages if not isinstance(m, dict) or m.get("role") != "system"]

    # Serialise any OpenAI message objects to plain dicts
    serialisable_history = []
    for m in updated_history:
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
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
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
    }
