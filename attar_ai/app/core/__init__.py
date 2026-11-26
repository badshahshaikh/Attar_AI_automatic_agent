"""
core/__init__.py
----------------
Core package exports.
"""

from attar_ai.app.core.config import settings, Settings
from attar_ai.app.core.logging import setup_logging, get_logger, log_request_start, log_request_complete, log_tool_call, log_tool_result
from attar_ai.app.core.exceptions import (
    AppException,
    ConfigurationError,
    ProviderError,
    ToolExecutionError,
    ValidationError,
    RateLimitError,
    InventoryError,
    RecommendationError,
    ConversationError,
)

__all__ = [
    "settings",
    "Settings",
    "setup_logging",
    "get_logger",
    "log_request_start",
    "log_request_complete",
    "log_tool_call",
    "log_tool_result",
    "AppException",
    "ConfigurationError",
    "ProviderError",
    "ToolExecutionError",
    "ValidationError",
    "RateLimitError",
    "InventoryError",
    "RecommendationError",
    "ConversationError",
]