"""
tools/recommendation_tool.py
----------------------------
Product recommendation tool for the agent.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from attar_ai.app.core.logging import get_logger
from attar_ai.app.repositories.sheets_repository import sheets_repository
from attar_ai.app.services.recommendation_service import recommendation_service
from attar_ai.app.schemas.recommendation import RecommendationResponse
from attar_ai.app.utils.normalization import normalize_price, normalize_size, normalize_stock
from attar_ai.app.utils.product_matching import verification_match

logger = get_logger(__name__)

# Tool schema for OpenAI function calling
RECOMMENDATION_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "recommend_products",
        "description": (
            "Recommend MS Fragrances products based on customer preferences, "
            "budget, scent profile, occasion, intensity, and product type. "
            "Use if the customer wants suggestions or help choosing a product."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "budget": {"type": "number", "description": "Maximum budget in INR"},
                "scent_family": {"type": "array", "items": {"type": "string"}},
                "intensity": {"type": "string", "enum": ["light", "moderate", "strong"]},
                "occasion": {"type": "array", "items": {"type": "string"}},
                "preferred_notes": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 3},
            },
        },
    },
}


def recommend_products_tool(arguments: dict[str, Any]) -> str:
    """
    Execute the recommend_products tool call.

    Runs the deterministic recommendation engine, then verifies each candidate
    against the live Sheets lookup. Verification prefers an exact product_id
    match, then an exact normalized product name, then a verified alias; any
    other outcome is rejected as ambiguous or not found.

    Returns:
        JSON string with validated recommendation response.
    """
    try:
        budget = arguments.get("budget")
        if budget is not None:
            budget = float(budget)

        limit = arguments.get("limit", 3)
        if limit is not None:
            limit = int(limit)

        results = recommendation_service.recommend_products(
            budget=budget,
            scent_family=arguments.get("scent_family"),
            intensity=arguments.get("intensity"),
            occasion=arguments.get("occasion"),
            preferred_notes=arguments.get("preferred_notes"),
            limit=limit,
        )
    except Exception as exc:
        logger.exception("recommendation engine error")
        return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    verified_at = datetime.now(timezone.utc).isoformat()
    verified_products = []

    for rec in results:
        product_name = rec.get("product_name", "")

        # Fetch live sheet rows for this product
        sheet_rows: list[dict] = []
        try:
            sheet_result = json.loads(sheets_repository.lookup_product(product_name=product_name))
        except Exception:
            sheet_result = []
        if isinstance(sheet_result, list):
            sheet_rows = [r for r in sheet_result if isinstance(r, dict)]

        match, kind = verification_match(sheet_rows, rec)

        price = normalize_price(rec.get("price_min"))
        size = (rec.get("available_sizes") or [None])[0]
        in_stock = False
        status = "not_found"

        if kind == "single":
            live_price = normalize_price(match.get("price") or match.get("price_inr"))
            live_size = match.get("size") or match.get("size_ml")
            in_stock = normalize_stock(
                match.get("stock_quantity")
                if match.get("stock_quantity") is not None
                else match.get("in_stock")
            )

            if not in_stock:
                status = "out_of_stock"
            else:
                if live_price is not None and price is not None and live_price != price:
                    status = "price_changed"
                    price = live_price
                else:
                    status = "verified"
                    if live_price is not None:
                        price = live_price

            if live_size:
                size = str(live_size)

        elif kind == "ambiguous":
            status = "ambiguous_match"
        # kind == "not_found" keeps status = "not_found" with catalog fallbacks

        verified_products.append(
            {
                "product_id": rec.get("product_id"),
                "product_name": product_name,
                "matched_attributes": rec.get("matched_attributes", []),
                "price": price,
                "size": size,
                "in_stock": in_stock,
                "reason": rec.get("reason", ""),
                "verification_status": status,
                "verified_at": verified_at,
                "verification": {"status": status, "verified_at": verified_at},
            }
        )

    payload = {"status": "success", "products": verified_products}

    try:
        validated = RecommendationResponse(**payload)
        return json.dumps(validated.model_dump(), ensure_ascii=False)
    except Exception:
        logger.exception("Recommendation output validation failed")
        return json.dumps(
            {"status": "error", "message": "Recommendation output validation failed", "products": []},
            ensure_ascii=False,
        )


def get_recommendation_tool_schema() -> dict:
    """Get the recommendation tool schema for OpenAI function calling."""
    return RECOMMENDATION_TOOL_SCHEMA