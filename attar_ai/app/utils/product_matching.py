"""
utils/product_matching.py
-------------------------
Product matching utilities for verification against live inventory.
"""

from typing import Any

from attar_ai.app.utils.normalization import normalize_text, normalize_size


def verification_match(sheet_rows: list[dict], rec: dict) -> tuple[dict | None, str]:
    """
    Match a recommendation against live sheet rows.

    Returns:
        tuple: (matched_row, match_kind) where match_kind is 'single', 'ambiguous', or 'not_found'
    """
    rec_id = str(rec.get("product_id") or "").strip()
    norm_name = normalize_text(rec.get("product_name"))
    rec_size = normalize_size(rec.get("size"))

    if not rec_size:
        sizes = rec.get("available_sizes") or []
        rec_size = normalize_size(sizes[0] if sizes else None)

    def by_product_id() -> list[dict]:
        if not rec_id:
            return []
        return [r for r in sheet_rows if str(r.get("product_id") or "").strip() == rec_id]

    def by_name_and_size() -> list[dict]:
        return [
            r
            for r in sheet_rows
            if normalize_text(r.get("product_name")) == norm_name
            and normalize_size(r.get("size") or r.get("size_ml")) == rec_size
        ]

    def by_product_name() -> list[dict]:
        return [r for r in sheet_rows if normalize_text(r.get("product_name")) == norm_name]

    def by_alias() -> list[dict]:
        matched = []
        for row in sheet_rows:
            aliases = str(row.get("aliases") or "")
            for token in aliases.split(","):
                if normalize_text(token) and normalize_text(token) == norm_name:
                    matched.append(row)
                    break
        return matched

    for matcher in (by_product_id, by_name_and_size, by_product_name, by_alias):
        matches = matcher()
        if len(matches) == 1:
            return matches[0], "single"
        if len(matches) > 1:
            return None, "ambiguous"

    return None, "not_found"