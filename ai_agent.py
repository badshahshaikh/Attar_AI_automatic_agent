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
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv

# Google Sheets lookup is the live inventory source
from sheets_lookup import lookup_product, LOOKUP_TOOL_SCHEMA

# Recommendation engine — deterministic product discovery
from recommendation_engine import recommend_products as _recommend_products

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# LLM provider selection (mirrors ms_fragrance_backend's PRODUCT_TEXT_PROVIDER)
# ---------------------------------------------------------------------------
# LLM_PROVIDER: "openai" (default) or "cloudflare".
# Cloudflare Workers AI is used via its OpenAI-compatible endpoint so the
# existing tool-calling (function calling) loop keeps working unchanged.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "cloudflare").strip().lower()

# OpenAI settings (used when LLM_PROVIDER == "openai")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT = 30.0
try:
    OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "30"))
except (TypeError, ValueError):
    OPENAI_TIMEOUT = 30.0

# Cloudflare Workers AI settings (used when LLM_PROVIDER == "cloudflare")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
CLOUDFLARE_MODEL = os.getenv(
    "CLOUDFLARE_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
).strip()
CLOUDFLARE_TIMEOUT = 60.0
try:
    CLOUDFLARE_TIMEOUT = float(os.getenv("CLOUDFLARE_TIMEOUT", "60"))
except (TypeError, ValueError):
    CLOUDFLARE_TIMEOUT = 60.0

# Resolve the active model name and build the (OpenAI-compatible) client.
if LLM_PROVIDER == "cloudflare":
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        raise RuntimeError(
            "LLM_PROVIDER=cloudflare requires CLOUDFLARE_ACCOUNT_ID and "
            "CLOUDFLARE_API_TOKEN in .env."
        )
    OPENAI_MODEL = CLOUDFLARE_MODEL
    _client = OpenAI(
        api_key=CLOUDFLARE_API_TOKEN,
        base_url=(
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{CLOUDFLARE_ACCOUNT_ID}/ai/v1"
        ),
        timeout=CLOUDFLARE_TIMEOUT,
    )
else:
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=OPENAI_TIMEOUT)

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")

# Hard cap on how many history entries are sent to the model. Keeps token usage
# bounded no matter how long a client keeps the conversation going.
MAX_HISTORY_TURNS = 20


def _load_system_prompt() -> str:
    """Read system_prompt.txt fresh each request so manual edits take effect immediately."""
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# OpenAI function-calling schemas
# ---------------------------------------------------------------------------

RECOMMEND_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "recommend_products",
        "description": (
            "Recommend MS Fragrances products based on customer preferences, "
            "budget, scent profile, occasion, intensity, and product type. "
            "Use if the customer wants suggestions or help choosing a product."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "budget": {"type": "number", "description": "Maximum budget in INR"},
                "scent_family": {"type": "array", "items": {"type": "string"}},
                "intensity": {"type": "string", "enum": ["light", "moderate", "strong"]},
                "occasion": {"type": "array", "items": {"type": "string"}},
                "preferred_notes": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 3},
            },
        },
    },
}


def _normalize_text(val: Any) -> str:
    """Collapse whitespace and lowercase for case-insensitive comparison."""
    return " ".join(str(val or "").strip().lower().split())


def _normalize_size(val):
    return str(val or '').strip().lower().replace('ml', '').strip()


def _verification_match(
    sheet_rows, rec
):
    rec_id = str(rec.get('product_id') or '').strip()
    norm_name = _normalize_text(rec.get('product_name'))
    rec_size = _normalize_size(rec.get('size'))
    if not rec_size:
        _sizes = rec.get('available_sizes') or []
        rec_size = _normalize_size(_sizes[0] if _sizes else None)

    def by_product_id():
        if not rec_id:
            return []
        return [r for r in sheet_rows if str(r.get('product_id') or '').strip() == rec_id]

    def by_name_and_size():
        return [r for r in sheet_rows if _normalize_text(r.get('product_name')) == norm_name and _normalize_size(r.get('size') or r.get('size_ml')) == rec_size]

    def by_product_name():
        return [r for r in sheet_rows if _normalize_text(r.get('product_name')) == norm_name]

    def by_alias():
        matched = []
        for row in sheet_rows:
            aliases = str(row.get('aliases') or '')
            for token in aliases.split(','):
                if _normalize_text(token) and _normalize_text(token) == norm_name:
                    matched.append(row)
                    break
        return matched

    for matcher in (by_product_id, by_name_and_size, by_product_name, by_alias):
        matches = matcher()
        if len(matches) == 1:
            return matches[0], 'single'
        if len(matches) > 1:
            return None, 'ambiguous'
    return None, 'not_found'


def _live_price(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _live_stock_ok(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    if text in ("", "false", "0", "no", "none", "null", "n/a"):
        return False
    if text in ("true", "yes", "1", "y", "available", "in stock"):
        return True
    try:
        return float(text) > 0
    except (TypeError, ValueError):
        return False


def _handle_recommend_products(args: dict) -> str:
    """
    Execute a recommend_products tool call.

    Runs the deterministic recommendation engine, then verifies each candidate
    against the live Sheets lookup. Verification prefers an exact product_id
    match, then an exact normalized product name, then a verified alias; any
    other outcome is rejected as ambiguous or not found.

    Returns a structured JSON payload validated against the Pydantic models
    defined in main.py.
    """
    try:
        budget = args.get("budget")
        if budget is not None:
            budget = float(budget)

        limit = args.get("limit", 3)
        if limit is not None:
            limit = int(limit)

        results = _recommend_products(
            budget=budget,
            scent_family=args.get("scent_family"),
            intensity=args.get("intensity"),
            occasion=args.get("occasion"),
            preferred_notes=args.get("preferred_notes"),
            limit=limit,
        )
    except Exception as exc:
        logger.exception("recommendation engine error")
        return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    verified_at = datetime.now(timezone.utc).isoformat()
    verified: list[dict] = []

    for rec in results:
        product_name = rec.get("product_name", "")

        # Fetch live sheet rows for this product
        sheet_rows: list[dict] = []
        try:
            sheet_result = json.loads(lookup_product(product_name=product_name))
        except Exception:
            sheet_result = []
        if isinstance(sheet_result, list):
            sheet_rows = [r for r in sheet_result if isinstance(r, dict)]

        match, kind = _verification_match(sheet_rows, rec)

        price = _live_price(rec.get("price_min"))
        size = (rec.get("available_sizes") or [None])[0]
        in_stock = False
        status = "not_found"

        if kind == "single":
            live_price = _live_price(match.get("price") or match.get("price_inr"))
            live_size = match.get("size") or match.get("size_ml")
            in_stock = _live_stock_ok(
                match.get("stock_quantity")
                if match.get("stock_quantity") is not None
                else match.get("in_stock")
            )

            if not in_stock:
                status = "out_of_stock"
            else:
                if live_price is not None and price is not None and live_price != price:
                    status = "price_changed"
                    price = live_price
                else:
                    status = "verified"
                    if live_price is not None:
                        price = live_price

            if live_size:
                size = str(live_size)

        elif kind == "ambiguous":
            status = "ambiguous_match"
        # kind == "not_found" keeps status = "not_found" with catalog fallbacks

        verified.append(
            {
                "product_id": rec.get("product_id"),
                "product_name": product_name,
                "matched_attributes": rec.get("matched_attributes", []),
                "price": price,
                "size": size,
                "in_stock": in_stock,
                "reason": rec.get("reason", ""),
                "verification_status": status,
                "verified_at": verified_at,
                "verification": {"status": status, "verified_at": verified_at},
            }
        )

    payload = {"status": "success", "products": verified}
    try:
        # Validate tool output against the Pydantic models defined in main.py.
        # Imported lazily to avoid a circular import (main.py imports ai_agent).
        from main import RecommendationResponse

        validated = RecommendationResponse(**payload)
        return json.dumps(validated.model_dump(), ensure_ascii=False)
    except Exception:
        logger.exception("Recommendation output validation failed")
        return json.dumps(
            {"status": "error", "message": "Recommendation output validation failed", "products": []},
            ensure_ascii=False,
        )


def _new_order_session():
    """Create a new order collection session."""
    import json
    session_id = str(json.loads('"0"'))  # simple unique ID
    _order_sessions[session_id] = {
        'customer': {},
        'products': [],  # list of {product_name, size, quantity, price}
        'step': 'name',
    }
    return session_id


def _get_order_session():
    """Get the current order session, or create a new one."""
    if not _order_sessions:
        return _new_order_session()
    # Return the most recent session
    return list(_order_sessions.keys())[-1]


def _check_duplicate_order(session_id, order_id):
    """Check if an order ID already exists to prevent duplicates."""
    import json
    from sheets_lookup import _build_sheets_service
    import os

    try:
        service = _build_sheets_service()
        sheet_id = os.getenv('GOOGLE_SHEET_ID', '').strip()
        if not sheet_id:
            return False  # Can't check without sheet ID

        # Read the sheet to check for the order ID
        # Read first column (order IDs)
        range_name = f"'{os.getenv('GOOGLE_SHEET_NAME', 'Products')}!'!A:A"
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        values = result.get('values', [])
        if values:
            for row in values[1:]:  # Skip header
                if len(row) > 0 and str(row[0]).strip() == str(order_id).strip():
                    return True
        return False
    except Exception:
        # If we can't check, assume no duplicate (with warning)
        return False

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

    # Gracefully reject empty / non-string input instead of sending it to the model.
    if not isinstance(message, str) or not message.strip():
        obs["error"] = "empty_message"
        obs["duration_ms"] = round((time.monotonic() - t_start) * 1000)
        logger.warning("chat() rejected an empty or invalid message")
        return {
            "customer_message": message if isinstance(message, str) else "",
            "reply": "Please type a message so I can help you.",
            "tool_calls_made": [],
            "tool_results": [],
            "updated_history": history or [],
            "observability": obs,
        }

    history = history or []

    # Cap the conversation to the most recent turns to avoid token blowup.
    if len(history) > MAX_HISTORY_TURNS:
        logger.info(
            "trimming history from %d to %d entries", len(history), MAX_HISTORY_TURNS
        )
        history = history[-MAX_HISTORY_TURNS:]

    system_prompt = _load_system_prompt()

    # Build messages list
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    tool_calls_made: list[dict] = []
    tool_results: list[dict] = []
    final_reply = ""
    _seen_tool_calls: set[str] = set()
    _tool_rounds = 0
    _force_answer = False
    _force_answer_injected = False

    try:
        # ---- Agentic loop: iterate until the model stops calling tools ------
        MAX_ITERATIONS = 10
        for _ in range(MAX_ITERATIONS):
            obs["openai_called"] = True
            # Once we have retrieved tool results, force the model to answer
            # instead of looping on further tool calls (common with weaker models).
            create_kwargs = dict(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.2,
            )
            if _force_answer:
                create_kwargs["tool_choice"] = "none"
                if not _force_answer_injected:
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "You already have the inventory information above. "
                                "Now provide your final answer to the customer. "
                                "Do not call any more tools."
                            ),
                        }
                    )
                    _force_answer_injected = True
                    create_kwargs["messages"] = messages
            else:
                create_kwargs["tools"] = [LOOKUP_TOOL_SCHEMA, RECOMMEND_TOOL_SCHEMA]
                create_kwargs["tool_choice"] = "auto"

            response = _client.chat.completions.create(**create_kwargs)

            assistant_message = response.choices[0].message
            # Cloudflare's OpenAI-compatible endpoint rejects null `content`
            # (OpenAI allows it when tool_calls are present). Normalize to "".
            assistant_entry = {
                "role": "assistant",
                "content": assistant_message.content or "",
            }
            if getattr(assistant_message, "tool_calls", None):
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
            messages.append(assistant_entry)

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
                    fn_args = (
                        json.loads(tc.function.arguments) if tc.function.arguments else {}
                    )
                except (json.JSONDecodeError, TypeError):
                    fn_args = {}
                if not isinstance(fn_args, dict):
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

                # Guard against the model repeating the exact same tool call forever.
                call_signature = fn_name + "::" + json.dumps(fn_args, sort_keys=True, ensure_ascii=False)
                if call_signature in _seen_tool_calls:
                    logger.warning("Duplicate tool call detected, forcing final answer: %s", call_signature)
                    _force_answer = True
                    result_json = json.dumps(
                        {"note": "This lookup was already performed. Use the previous result and answer the customer now."}
                    )
                else:
                    _seen_tool_calls.add(call_signature)
                    try:
                        if fn_name == "lookup_product":
                            result_json = lookup_product(
                                product_name=fn_args.get("product_name", ""),
                                size=fn_args.get("size"),
                            )
                        elif fn_name == "recommend_products":
                            result_json = _handle_recommend_products(fn_args)
                        else:
                            result_json = json.dumps({"error": f"Unknown tool: {fn_name}"})
                    except Exception as exc:
                        # Sheets timeout, network failure, or any other tool error:
                        # record a structured error result and keep the loop going.
                        logger.exception("Tool execution failed | fn=%s", fn_name)
                        result_json = json.dumps(
                            {"error": f"Tool execution failed: {exc}"}, ensure_ascii=False
                        )

                # Invalid JSON from a tool is treated as an error result
                # rather than crashing the agent loop.
                try:
                    parsed_result = json.loads(result_json)
                except (json.JSONDecodeError, TypeError):
                    parsed_result = {"error": "Tool returned invalid JSON"}
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
            _tool_rounds += 1
            if _tool_rounds >= 2:
                _force_answer = True

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
