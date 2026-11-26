"""
api/routes/health.py
--------------------
Health check API endpoint.
"""

import logging
from fastapi import APIRouter

from attar_ai.app.core.logging import get_logger
from attar_ai.app.schemas.chat import HealthResponse

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        message="MS Fragrances AI Agent v2 is running.",
    )