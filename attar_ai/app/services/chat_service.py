"""
services/chat_service.py
------------------------
Main chat service coordinating the complete workflow.
"""

import logging
from typing import Any

from attar_ai.app.agents.customer_agent import CustomerAgent
from attar_ai.app.agents.tool_registry import ToolRegistry
from attar_ai.app.core.config import settings
from attar_ai.app.core.logging import get_logger
from attar_ai.app.schemas.chat import ChatResponse, ObservabilityInfo
from attar_ai.app.services.conversation_service import conversation_service
from attar_ai.app.tools.inventory_tool import lookup_product_tool, get_inventory_tool_schema
from attar_ai.app.tools.recommendation_tool import recommend_products_tool, get_recommendation_tool_schema

logger = get_logger(__name__)


class ChatService:
    """Coordinate the complete chat workflow."""

    def __init__(self):
        # Initialize tool registry with available tools
        self.tool_registry = ToolRegistry()
        self._register_tools()

        # Initialize customer agent
        self.agent = CustomerAgent(self.tool_registry)

    def _register_tools(self) -> None:
        """Register all available tools with the tool registry."""
        self.tool_registry.register(
            "lookup_product",
            lookup_product_tool,
            get_inventory_tool_schema(),
        )
        self.tool_registry.register(
            "recommend_products",
            recommend_products_tool,
            get_recommendation_tool_schema(),
        )
        logger.info("Registered tools: %s", self.tool_registry.list_tools())

    def process_message(
        self,
        message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> ChatResponse:
        """
        Process a customer message and return a structured response.

        Args:
            message: The customer's message.
            history: Previous conversation history.

        Returns:
            ChatResponse with the agent's reply and metadata.
        """
        # Validate and trim history
        history = conversation_service.validate_history(history or [])
        history = conversation_service.trim_history(history, settings.max_history_turns)

        # Run the agent
        (
            reply,
            tool_calls_made,
            tool_results,
            updated_history,
            observability,
        ) = self.agent.run(message=message, history=history)

        return ChatResponse(
            customer_message=message,
            reply=reply,
            tool_calls_made=tool_calls_made,
            tool_results=tool_results,
            updated_history=updated_history,
            observability=observability,
        )


# Global service instance
chat_service = ChatService()