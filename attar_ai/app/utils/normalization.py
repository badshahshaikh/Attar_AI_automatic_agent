"""
utils/normalization.py
----------------------
Text and data normalization utilities.
"""

from typing import Any


def normalize_text(val: Any) -> str:
    """Collapse whitespace and lowercase for case-insensitive comparison."""
    return " ".join(str(val or "").strip().lower().split())


def normalize_size(val: Any) -> str:
    """Normalize size value by removing 'ml' and whitespace."""
    return str(val or "").strip().lower().replace("ml", "").strip()


def normalize_price(value: Any) -> float | None:
    """Convert a value to float price, returning None if invalid."""
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_stock(value: Any) -> bool:
    """Convert a stock value to boolean availability."""
    if value is None:
        return False
    text = str(value).strip().lower()
    if text in ("", "false", "0", "no", "none", "null", "n/a"):
        return False
    if text in ("true", "yes", "1", "y", "available", "in stock"):
        return True
    try:
        return float(text) > 0
    except (TypeError, ValueError):
        return False


def normalize_list(val: list[str] | None) -> list[str]:
    """Normalize a list of strings to lowercase, stripped."""
    if not val:
        return []
    return [v.strip().lower() for v in val if v]