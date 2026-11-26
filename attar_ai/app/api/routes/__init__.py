"""
api/routes/__init__.py
----------------------
API routes package exports.
"""

from attar_ai.app.api.routes.chat import router as chat_router
from attar_ai.app.api.routes.health import router as health_router

__all__ = [
    "chat_router",
    "health_router",
]