"""
core/exceptions.py
------------------
Custom application exceptions.
"""


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str):
        super().__init__(message, code="CONFIGURATION_ERROR")


class ProviderError(AppException):
    """Raised when LLM provider returns an error."""

    def __init__(self, message: str, provider: str, status_code: int | None = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(message, code="PROVIDER_ERROR")


class ToolExecutionError(AppException):
    """Raised when a tool execution fails."""

    def __init__(self, message: str, tool_name: str):
        self.tool_name = tool_name
        super().__init__(message, code="TOOL_EXECUTION_ERROR")


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message, code="VALIDATION_ERROR")


class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int):
        self.retry_after = retry_after
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")


class InventoryError(AppException):
    """Raised when inventory lookup fails."""

    def __init__(self, message: str):
        super().__init__(message, code="INVENTORY_ERROR")


class RecommendationError(AppException):
    """Raised when recommendation generation fails."""

    def __init__(self, message: str):
        super().__init__(message, code="RECOMMENDATION_ERROR")


class ConversationError(AppException):
    """Raised when conversation handling fails."""

    def __init__(self, message: str):
        super().__init__(message, code="CONVERSATION_ERROR")