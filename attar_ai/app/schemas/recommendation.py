"""
schemas/recommendation.py
-------------------------
Recommendation tool output schemas.
"""

from typing import Literal

from pydantic import BaseModel, Field


VerificationStatus = Literal[
    "verified",
    "price_changed",
    "out_of_stock",
    "not_found",
    "ambiguous_match",
    "verification_failed",
]


class VerificationResult(BaseModel):
    """Verification result against live inventory."""

    status: VerificationStatus = Field(
        description="Verification outcome of the recommended product against the live inventory sheet."
    )
    verified_at: str = Field(
        description="ISO-8601 UTC timestamp when the verification was performed."
    )


class RecommendationProduct(BaseModel):
    """A verified product recommendation."""

    product_id: str | None = Field(
        default=None, description="Catalog product ID of the recommended product."
    )
    product_name: str = Field(description="Recommended product name.")
    matched_attributes: list[str] = Field(
        default_factory=list,
        description="Catalog attributes that matched the customer's preferences.",
    )
    price: float | None = Field(
        default=None,
        description="Verified live price in INR, falling back to the catalog price_min.",
    )
    size: str | None = Field(
        default=None,
        description="Verified live size, falling back to the first available catalog size.",
    )
    in_stock: bool = Field(default=False, description="Whether the verified size is in stock.")
    reason: str = Field(default="", description="Human-readable match reason.")
    verification_status: VerificationStatus = Field(
        description="Verification outcome of the recommended product against the live inventory sheet."
    )
    verified_at: str = Field(
        description="ISO-8601 UTC timestamp when the verification was performed."
    )
    verification: VerificationResult = Field(
        description="Nested verification result against the live inventory sheet."
    )


class RecommendationResponse(BaseModel):
    """Response from the recommend_products tool."""

    status: Literal["success", "error"] = Field(default="success")
    products: list[RecommendationProduct] = Field(default_factory=list)
    message: str | None = Field(
        default=None, description="Error message when status is 'error'."
    )


class ToolErrorResponse(BaseModel):
    """Structured error response for a failed tool call."""

    error: dict[str, str] = Field(
        description="Structured error with code and message."
    )