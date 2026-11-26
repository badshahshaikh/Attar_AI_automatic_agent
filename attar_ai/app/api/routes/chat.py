"""
api/routes/chat.py
------------------
Chat API endpoint.
"""

import logging
from fastapi import APIRouter, HTTPException

from attar_ai.app.core.config import settings
from attar_ai.app.core.logging import get_logger
from attar_ai.app.schemas.chat import ChatRequest, ChatResponse
from attar_ai.app.services.chat_service import chat_service

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Agent"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
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

    if request.message is None or len(request.message) > settings.max_message_length:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Message exceeds the maximum length of "
                f"{settings.max_message_length} characters."
            ),
        )

    try:
        result = chat_service.process_message(
            message=request.message,
            history=request.history,
        )
        return result
    except Exception as exc:
        logger.exception("Unhandled error in /chat endpoint")
        raise HTTPException(status_code=500, detail=str(exc))