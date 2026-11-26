"""
core/logging.py
---------------
Centralized logging configuration.
"""

import logging
import sys
from typing import Any

from attar_ai.app.core.config import settings


def setup_logging() -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("google_auth_httplib2").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given module name."""
    return logging.getLogger(name)


def log_request_start(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log the start of a request with structured data."""
    logger.info("request_start | message_preview=%.80s | %s", message, _format_kwargs(kwargs))


def log_request_complete(
    logger: logging.Logger,
    duration_ms: int,
    provider: str,
    model: str,
    tool_calls: int,
    error: str | None = None,
    **kwargs: Any,
) -> None:
    """Log the completion of a request with structured observability data."""
    logger.info(
        "request_complete | duration_ms=%d | provider=%s | model=%s | tool_calls=%d | error=%s | %s",
        duration_ms,
        provider,
        model,
        tool_calls,
        error,
        _format_kwargs(kwargs),
    )


def log_tool_call(logger: logging.Logger, provider: str, fn_name: str, args: dict) -> None:
    """Log a tool call."""
    logger.info("tool_call | provider=%s | fn=%s | args=%s", provider, fn_name, args)


def log_tool_result(logger: logging.Logger, provider: str, fn_name: str, result_type: str) -> None:
    """Log a tool result."""
    logger.info("tool_result | provider=%s | fn=%s | result_type=%s", provider, fn_name, result_type)


def _format_kwargs(kwargs: dict[str, Any]) -> str:
    """Format keyword arguments for logging."""
    return " | ".join(f"{k}={v}" for k, v in kwargs.items())