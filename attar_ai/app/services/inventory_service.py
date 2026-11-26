"""
services/inventory_service.py
-----------------------------
Inventory business logic service.
"""

import json
import logging
from typing import Any

from attar_ai.app.core.logging import get_logger
from attar_ai.app.repositories.sheets_repository import sheets_repository
from attar_ai.app.schemas.product import ProductLookupResult

logger = get_logger(__name__)


class InventoryService:
    """Handle product lookup, price, and stock-related business logic."""

    def __init__(self):
        self.repository = sheets_repository

    def lookup_product(self, product_name: str, size: str | None = None) -> list[dict]:
        """
        Look up a product in the live inventory.

        Args:
            product_name: The product name or alias to search for.
            size: Optional size filter.

        Returns:
            List of matching product dictionaries.
        """
        try:
            result_json = self.repository.lookup_product(product_name=product_name, size=size)
            result = json.loads(result_json)
            if isinstance(result, list):
                return [r for r in result if isinstance(r, dict)]
            elif isinstance(result, dict) and "error" in result:
                logger.error("Inventory lookup error: %s", result["error"])
                return []
            return []
        except Exception as exc:
            logger.exception("Inventory lookup failed")
            return []

    def get_product_price(self, product_name: str, size: str | None = None) -> float | None:
        """Get the price for a specific product and size."""
        products = self.lookup_product(product_name, size)
        if not products:
            return None
        # Return the first matching product's price
        product = products[0]
        price = product.get("price") or product.get("price_inr")
        if price is not None:
            try:
                return float(price)
            except (TypeError, ValueError):
                pass
        return None

    def is_in_stock(self, product_name: str, size: str | None = None) -> bool:
        """Check if a product is in stock."""
        products = self.lookup_product(product_name, size)
        if not products:
            return False
        product = products[0]
        stock = product.get("stock_quantity")
        if stock is None:
            stock = product.get("in_stock")
        if stock is not None:
            try:
                return float(stock) > 0
            except (TypeError, ValueError):
                pass
        return False

    def get_all_products(self) -> list[dict]:
        """Get all products from the inventory."""
        return self.repository.fetch_all_products()


# Global service instance
inventory_service = InventoryService()