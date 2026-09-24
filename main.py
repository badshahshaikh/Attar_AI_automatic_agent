"""
main.py
-------
FastAPI app exposing a single POST /chat endpoint for manual testing.
Open http://localhost:8000/docs to test via Swagger UI.
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Any

from ai_agent import chat

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MS Fragrances AI Product Assistant",
    description=(
        "Send customer messages to the AI agent and inspect its replies, "
        "tool calls, and product lookup results. "
        "Use the **POST /chat** endpoint below."
    ),
    version="1.0.0",
)

# Allow all origins so the static HTML frontend can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


class ChatResponse(BaseModel):
    customer_message: str = Field(description="The original customer message.")
    reply: str = Field(description="The AI agent's final reply to the customer.")
    tool_calls_made: list[dict[str, Any]] = Field(
        description="List of product lookups the AI requested (tool name + arguments)."
    )
    tool_results: list[dict[str, Any]] = Field(
        description="The actual inventory data returned for each lookup."
    )
    updated_history: list[dict[str, Any]] = Field(
        description="Full conversation history. Pass this back in the next request for follow-up questions."
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
    return {"status": "ok", "message": "MS Fragrances AI Agent is running."}


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
def chat_endpoint(request: ChatRequest):
    """
    Send a customer message to the AI Product Assistant and receive a structured response.

    **How to use follow-up questions:**
    1. Send your first message with `history: []`.
    2. Copy the `updated_history` from the response.
    3. On your next message, paste that history into the `history` field.
    4. The agent will remember the conversation context.
    """
    try:
        result = chat(message=request.message, history=request.history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
