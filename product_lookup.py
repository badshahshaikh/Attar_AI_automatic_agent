"""
product_lookup.py
-----------------
Loads the Excel inventory and provides a lookup function that the AI agent
can call via function-calling. Returns matching product rows as plain dicts
so the AI can ground every answer in real data.
"""

import os
import json
import pandas as pd

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "data", "products.xlsx")

# ---------------------------------------------------------------------------
# Load the workbook once at import time
# ---------------------------------------------------------------------------

def _load_products() -> pd.DataFrame:
    """Read products.xlsx and normalise column names."""
    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    # Normalise column names: lower-case, spaces → underscores
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


try:
    _PRODUCTS_DF = _load_products()
except FileNotFoundError:
    _PRODUCTS_DF = pd.DataFrame()


# ---------------------------------------------------------------------------
# Public lookup function — called by the AI agent
# ---------------------------------------------------------------------------

def lookup_product(product_name: str, size: str | None = None) -> str:
    """
    Search the inventory for a product by name (and optionally size).

    Parameters
    ----------
    product_name : str
        The product name or alias the customer mentioned.
    size : str | None
        Optional size filter, e.g. "6ml", "12ml", "3ml".

    Returns
    -------
    str
        A JSON string containing a list of matching product dicts.
        Returns an empty list JSON "[]" when nothing is found.
    """

    if _PRODUCTS_DF.empty:
        return json.dumps({"error": "Product database not loaded. Check data/products.xlsx."})

    df = _PRODUCTS_DF.copy()

    # ---- Name / alias matching (case-insensitive substring) ----------------
    name_lower = product_name.strip().lower()
    mask_name = df["product_name"].str.lower().str.contains(name_lower, na=False)

    # Also search aliases column if it exists
    if "aliases" in df.columns:
        mask_alias = df["aliases"].str.lower().str.contains(name_lower, na=False)
        mask_name = mask_name | mask_alias

    df = df[mask_name]

    # ---- Optional size filter -----------------------------------------------
    if size and not df.empty:
        size_lower = size.strip().lower()
        if "size" in df.columns:
            df = df[df["size"].astype(str).str.lower().str.contains(size_lower, na=False)]

    # ---- Return results -----------------------------------------------------
    if df.empty:
        return json.dumps([])

    # Convert to list of dicts, replacing NaN with None for clean JSON
    records = df.where(pd.notnull(df), None).to_dict(orient="records")
    return json.dumps(records, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# OpenAI function-calling schema for this tool
# ---------------------------------------------------------------------------

LOOKUP_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "lookup_product",
        "description": (
            "Search the MS Fragrances inventory for a product. "
            "Call this whenever you need product details such as price, "
            "stock, available sizes, or description. "
            "Always use real results — never guess."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "The product name or alias to search for (e.g. 'Oud', 'Rose Attar').",
                },
                "size": {
                    "type": "string",
                    "description": "Optional size to filter by (e.g. '6ml', '12ml'). Omit if not specified.",
                },
            },
            "required": ["product_name"],
        },
    },
}
