"""
services/recommendation_service.py
-----------------------------------
Product recommendation service.
"""

import logging
from typing import Any

from attar_ai.app.core.logging import get_logger
from recommendation_engine import recommend_products as _recommend_products

logger = get_logger(__name__)


class RecommendationService:
    """Handle product recommendations and live inventory verification."""

    def __init__(self):
        self.max_recommendations = 3

    def recommend_products(
        self,
        budget: float | None = None,
        scent_family: list[str] | None = None,
        intensity: str | None = None,
        occasion: list[str] | None = None,
        preferred_notes: list[str] | None = None,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Recommend products based on customer preferences.

        Args:
            budget: Maximum budget in INR.
            scent_family: Desired scent families.
            intensity: Desired intensity (light, moderate, strong).
            occasion: Desired occasions.
            preferred_notes: Preferred scent notes.
            limit: Maximum number of recommendations.

        Returns:
            List of recommended products with match details.
        """
        limit = min(limit, self.max_recommendations)

        try:
            results = _recommend_products(
                budget=budget,
                scent_family=scent_family,
                intensity=intensity,
                occasion=occasion,
                preferred_notes=preferred_notes,
                limit=limit,
            )
            return results
        except Exception as exc:
            logger.exception("Recommendation engine error")
            raise


# Global service instance
recommendation_service = RecommendationService()