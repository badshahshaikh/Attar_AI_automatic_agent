"""
schemas/product.py
------------------
Product-related schemas.
"""

from typing import Any

from pydantic import BaseModel, Field


class ProductLookupResult(BaseModel):
    """Result from a product inventory lookup."""

    product_id: str | None = Field(default=None)
    product_name: str = Field(default="")
    aliases: str | None = Field(default=None)
    size_ml: str | int | None = Field(default=None)
    size: str | int | None = Field(default=None)
    price: float | int | None = Field(default=None)
    price_inr: float | int | None = Field(default=None)
    stock_quantity: int | float | str | None = Field(default=None)
    in_stock: bool | str | None = Field(default=None)
    description: str | None = Field(default=None)
    # Allow extra fields from Google Sheets
    model_config = {"extra": "allow"}


class ProductRecommendation(BaseModel):
    """A single product recommendation from the catalog."""

    product_name: str = Field(description="Recommended product name.")
    product_id: str | None = Field(default=None, description="Catalog product ID.")
    scent_family: list[str] = Field(default_factory=list)
    scent_notes: list[str] = Field(default_factory=list)
    intensity: str | None = Field(default=None)
    longevity: str | None = Field(default=None)
    occasion: list[str] = Field(default_factory=list)
    season: list[str] = Field(default_factory=list)
    target_audience: str | None = Field(default=None)
    price_min: float = Field(description="Minimum price in INR.")
    available_sizes: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)
    matched_attributes: list[str] = Field(default_factory=list)
    reason: str = Field(default="")
    score: int = Field(default=0, exclude=True)

    model_config = {"extra": "allow"}