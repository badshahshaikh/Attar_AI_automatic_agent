"""
main.py
-------
FastAPI app exposing a single POST /chat endpoint for manual testing.
Open http://localhost:8000/ for the Chat UI or /docs for Swagger.
"""

import logging
import os
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Literal

from ai_agent import chat

# ---------------------------------------------------------------------------
# Logging — simple, structured, no secrets
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MS Fragrances AI Product Assistant",
    description=(
        "Send customer messages to the AI agent and inspect its replies, "
        "tool calls, product lookup results, and observability metrics. "
        "Use the **POST /chat** endpoint below."
    ),
    version="2.0.0",
)

# ---------------------------------------------------------------------------
# Hardening configuration (all overridable via environment variables)
# ---------------------------------------------------------------------------

def _int_env(name: str, default: int) -> int:
    """Read an integer env var, falling back to the default on bad input."""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


# Comma-separated list of allowed CORS origins.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000,https://attar-ai-automatic-agent-1.onrender.com",
    ).split(",")
    if o.strip()
] or ["*"]

# Per-client-IP request budget for /chat, and the max characters per message.
RATE_LIMIT_PER_MINUTE = _int_env("RATE_LIMIT_PER_MINUTE", 30)
MAX_MESSAGE_LENGTH = _int_env("MAX_MESSAGE_LENGTH", 2000)

_RATE_WINDOW_SECONDS = 60.0
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = Lock()


def _client_ip(request: Request) -> str:
    """Best-effort client IP, honouring a single-hop X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# In-memory per-IP rate limiter — only guards POST /chat
# ---------------------------------------------------------------------------

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/chat" and request.method == "POST":
        ip = _client_ip(request)
        now = time.monotonic()
        with _rate_lock:
            bucket = _rate_buckets[ip]
            # Drop timestamps that have aged out of the window.
            while bucket and now - bucket[0] >= _RATE_WINDOW_SECONDS:
                bucket.popleft()
            if len(bucket) >= RATE_LIMIT_PER_MINUTE:
                retry_after = max(1, int(_RATE_WINDOW_SECONDS - (now - bucket[0])))
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            "Rate limit exceeded. Please wait a moment "
                            "before sending more messages."
                        )
                    },
                    headers={"Retry-After": str(retry_after)},
                )
            bucket.append(now)
    return await call_next(request)


# CORS is registered AFTER the rate limiter so it becomes the outer middleware
# and still decorates 429 responses with the correct CORS headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
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
    duration_ms: int = Field(description="Total wall-clock time for this request in milliseconds.")
    openai_called: bool = Field(description="Whether the OpenAI API was called.")
    tool_called: bool = Field(description="Whether any agent tool was called (lookup_product or recommend_products).")
    lookup_args: list[dict[str, Any]] = Field(description="Arguments passed to each agent tool call.")
    error: str | None = Field(default=None, description="Error message if something went wrong, otherwise null.")


class ChatResponse(BaseModel):
    customer_message: str = Field(description="The original customer message.")
    reply: str = Field(description="The AI agent's final reply to the customer.")
    tool_calls_made: list[dict[str, Any]] = Field(
        description="List of inventory lookups the AI requested (tool name + arguments)."
    )
    tool_results: list[dict[str, Any]] = Field(
        description="The actual Google Sheets data returned for each lookup."
    )
    updated_history: list[dict[str, Any]] = Field(
        description="Full conversation history. Pass this back in the next request for follow-up questions."
    )
    observability: ObservabilityInfo = Field(
        description="Lightweight metrics for this request: timing, tool usage, and errors."
    )


# ---------------------------------------------------------------------------
# Recommendation tool output models
# ---------------------------------------------------------------------------

VerificationStatus = Literal[
    "verified",
    "price_changed",
    "out_of_stock",
    "not_found",
    "ambiguous_match",
    "verification_failed",
]


class VerificationResult(BaseModel):
    status: VerificationStatus = Field(
        description="Verification outcome of the recommended product against the live inventory sheet."
    )
    verified_at: str = Field(
        description="ISO-8601 UTC timestamp when the verification was performed."
    )


class RecommendationProduct(BaseModel):
    product_id: str | None = Field(
        default=None, description="Catalog product ID of the recommended product."
    )
    product_name: str = Field(description="Recommended product name.")
    matched_attributes: list[str] = Field(
        default_factory=list,
        description="Catalog attributes that matched the customer's preferences.",
    )
    price: float | None = Field(
        default=None,
        description="Verified live price in INR, falling back to the catalog price_min.",
    )
    size: str | None = Field(
        default=None,
        description="Verified live size, falling back to the first available catalog size.",
    )
    in_stock: bool = Field(default=False, description="Whether the verified size is in stock.")
    reason: str = Field(default="", description="Human-readable match reason.")
    verification_status: VerificationStatus = Field(
        description="Verification outcome of the recommended product against the live inventory sheet."
    )
    verified_at: str = Field(
        description="ISO-8601 UTC timestamp when the verification was performed."
    )
    verification: VerificationResult = Field(
        description="Nested verification result against the live inventory sheet."
    )


class RecommendationResponse(BaseModel):
    status: Literal["success", "error"] = Field(default="success")
    products: list[RecommendationProduct] = Field(default_factory=list)
    message: str | None = Field(
        default=None, description="Error message when status is 'error'."
    )


class ErrorDetail(BaseModel):
    code: str = Field(description="Short machine-readable error code.")
    message: str = Field(description="Human-readable error message.")


class ToolErrorResponse(BaseModel):
    error: ErrorDetail = Field(
        description="Structured error response for a failed tool call."
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["UI"], include_in_schema=False)
def serve_ui():
    """Serve the chat UI HTML file."""
    html_path = os.path.join(os.path.dirname(__file__), "chat_ui.html")
    return FileResponse(html_path, media_type="text/html")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "message": "MS Fragrances AI Agent v2 is running."}


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
def chat_endpoint(request: ChatRequest):
    """
    Send a customer message to the AI Product Assistant and receive a structured response.

    **Inventory source:** Live Google Sheet — changes are reflected immediately.

    **How to use follow-up questions:**
    1. Send your first message with `history: []`.
    2. Copy the `updated_history` from the response.
    3. On your next message, paste that history into the `history` field.
    4. The agent will remember the conversation context.

    **Observability:** Each response includes a small `observability` object
    with `duration_ms` and `tool_called` so you can verify the agent is hitting
    the live inventory sheet.
    """
    logger.info("POST /chat | message_preview=%.80s", request.message)

    if request.message is None or len(request.message) > MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Message exceeds the maximum length of "
                f"{MAX_MESSAGE_LENGTH} characters."
            ),
        )

    try:
        result = chat(message=request.message, history=request.history)
        return result
    except Exception as exc:
        logger.exception("Unhandled error in /chat endpoint")
        raise HTTPException(status_code=500, detail=str(exc))
