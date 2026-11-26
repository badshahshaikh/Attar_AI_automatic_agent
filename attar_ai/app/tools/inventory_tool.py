"""
tools/inventory_tool.py
-----------------------
Inventory lookup tool for the agent.
"""

import json
import logging
from typing import Any

from attar_ai.app.core.logging import get_logger
from attar_ai.app.repositories.sheets_repository import sheets_repository
from attar_ai.app.schemas.product import ProductLookupResult

logger = get_logger(__name__)

# Tool schema for OpenAI function calling
INVENTORY_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "lookup_product",
        "description": (
            "Search the live MS Fragrances Google Sheets inventory for a product. "
            "Call this whenever you need product details: price, stock, sizes, description. "
            "Results are always real-time from the sheet — never guess or invent information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": (
                        "The product name or alias to search for. "
                        "e.g. 'Oud', 'Rose', 'gulab'. "
                        "Use the customer's exact wording — the lookup handles spelling variations."
                    ),
                },
                "size": {
                    "type": "string",
                    "description": (
                        "Optional size to filter by, e.g. '6', '6ml', '12ml'. "
                        "Omit if the customer did not mention a size."
                    ),
                },
            },
            "required": ["product_name"],
        },
    },
}


def lookup_product_tool(arguments: dict[str, Any]) -> str:
    """
    Execute the lookup_product tool call.

    Args:
        arguments: Dictionary with 'product_name' and optional 'size' keys.

    Returns:
        JSON string with the lookup results.
    """
    product_name = arguments.get("product_name", "")
    size = arguments.get("size")

    if not product_name:
        return json.dumps({"error": "product_name is required"}, ensure_ascii=False)

    logger.info("Inventory lookup | product_name=%s | size=%s", product_name, size)

    try:
        result_json = sheets_repository.lookup_product(product_name=product_name, size=size)
        return result_json
    except Exception as exc:
        logger.exception("Inventory lookup failed")
        return json.dumps({"error": f"Inventory lookup failed: {exc}"}, ensure_ascii=False)


def get_inventory_tool_schema() -> dict:
    """Get the inventory tool schema for OpenAI function calling."""
    return INVENTORY_TOOL_SCHEMA