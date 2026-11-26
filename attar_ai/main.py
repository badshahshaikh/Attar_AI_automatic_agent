"""
main.py
-------
FastAPI app exposing the chat endpoint and serving the UI.
"""

import logging
import os
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from attar_ai.app.api import chat_router, health_router
from attar_ai.app.core.config import settings
from attar_ai.app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# App setup
app = FastAPI(
    title="MS Fragrances AI Product Assistant",
    description=(
        "Send customer messages to the AI agent and inspect its replies, "
        "tool calls, product lookup results, and observability metrics. "
        "Use the **POST /chat** endpoint below."
    ),
    version="2.0.0",
)

# Hardening configuration
def _int_env(name: str, default: int) -> int:
    """Read an integer env var, falling back to the default on bad input."""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default

# Use settings for CORS and rate limiting
ALLOWED_ORIGINS = settings.get_allowed_origins_list()
RATE_LIMIT_PER_MINUTE = settings.rate_limit_per_minute
MAX_MESSAGE_LENGTH = settings.max_message_length

_RATE_WINDOW_SECONDS = 60.0
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = Lock()


def _client_ip(request: Request) -> str:
    """Best-effort client IP, honouring a single-hop X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# Rate limiting middleware
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


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(health_router)


# Serve UI at root
@app.get("/", tags=["UI"], include_in_schema=False)
async def serve_ui():
    """Serve the chat UI HTML file."""
    # The chat_ui.html is in the project root
    project_root = os.path.dirname(os.path.dirname(__file__))
    html_path = os.path.join(project_root, "chat_ui.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="UI not found")


# Log startup info
logger.info(
    "Application started | provider=%s | model=%s",
    settings.llm_provider,
    settings.get_active_model(),
)