"""
api/__init__.py
---------------
API package exports.
"""

from attar_ai.app.api.routes import chat_router, health_router

__all__ = [
    "chat_router",
    "health_router",
]