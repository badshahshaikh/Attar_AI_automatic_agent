"""
recommendation_engine.py
------------------------
Product discovery and recommendation engine for MS Fragrances.

Loads a local product catalog with enriched attributes, filters by customer
preferences, ranks matches, and returns top recommendations.
"""

import json
from typing import Any


CATALOG: list[dict[str, Any]] = [
    {
        "product_name": "Oud Al Shams",
        "scent_family": ["Woody", "Oud"],
        "scent_notes": ["Woody", "smoky", "warm", "amber"],
        "intensity": "strong",
        "longevity": "Long lasting",
        "occasion": ["Evening", "Special occasion"],
        "season": ["Winter", "All season"],
        "product_id": "oud_al_shams",
        "target_audience": "Unisex",
        "price_min": 350,
        "available_sizes": ["3ml", "6ml", "12ml"],
        "description": "A rich and smoky Oud with warm amber base notes. Long-lasting and majestic.",
        "tags": ["oud", "woody", "bold", "evening", "smoky"],
    },
    {
        "product_name": "Rose Attar",
        "scent_family": ["Floral"],
        "scent_notes": ["Rose", "floral", "fresh", "dewy"],
        "intensity": "moderate",
        "longevity": "Long lasting",
        "occasion": ["Daily", "Evening"],
        "season": ["Spring", "Summer"],
        "product_id": "rose_attar",
        "target_audience": "Feminine",
        "price_min": 280,
        "available_sizes": ["3ml", "6ml", "12ml"],
        "description": "Pure distilled rose petals. Soft, fresh, and feminine with a dewy floral heart.",
        "tags": ["rose", "floral", "fresh", "feminine", "daily"],
    },
    {
        "product_name": "Musk Tahara",
        "scent_family": ["Musky"],
        "scent_notes": ["Musk", "sandalwood", "clean", "white musk"],
        "intensity": "light",
        "longevity": "Long lasting",
        "occasion": ["Daily", "Office"],
        "season": ["All season"],
        "product_id": "musk_tahara",
        "target_audience": "Unisex",
        "price_min": 300,
        "available_sizes": ["3ml", "6ml", "12ml"],
        "description": "Clean white musk with a hint of sandalwood. Ideal for everyday wear.",
        "tags": ["musk", "clean", "daily", "office", "sandalwood"],
    },
    {
        "product_name": "Kesar Chandan",
        "scent_family": ["Woody", "Spicy"],
        "scent_notes": ["Saffron", "sandalwood", "warm", "creamy"],
        "intensity": "moderate",
        "longevity": "Long lasting",
        "occasion": ["Special occasion", "Evening"],
        "season": ["All season"],
        "product_id": "kesar_chandan",
        "target_audience": "Unisex",
        "price_min": 480,
        "available_sizes": ["6ml", "12ml"],
        "description": "Warm saffron meets creamy sandalwood. A classic unisex attar for special occasions.",
        "tags": ["saffron", "sandalwood", "warm", "special occasion", "unisex"],
    },
    {
        "product_name": "Jasmine Night",
        "scent_family": ["Floral"],
        "scent_notes": ["Jasmine", "floral", "exotic", "intoxicating"],
        "intensity": "moderate",
        "longevity": "Long lasting",
        "occasion": ["Evening"],
        "season": ["Summer"],
        "product_id": "jasmine_night",
        "target_audience": "Feminine",
        "price_min": 260,
        "available_sizes": ["3ml", "6ml", "12ml"],
        "description": "Intoxicating jasmine absolute for evening wear. Floral and exotic.",
        "tags": ["jasmine", "floral", "evening", "exotic", "summer"],
    },
    {
        "product_name": "Black Oud",
        "scent_family": ["Woody", "Oud"],
        "scent_notes": ["Oud", "leather", "spice", "dark", "resinous"],
        "intensity": "strong",
        "longevity": "Long lasting",
        "occasion": ["Evening", "Special occasion"],
        "season": ["Winter"],
        "product_id": "black_oud",
        "target_audience": "Unisex",
        "price_min": 750,
        "available_sizes": ["6ml", "12ml"],
        "description": "Dark, resinous Oud blended with leather and spice. Bold and commanding.",
        "tags": ["oud", "woody", "leather", "spice", "bold", "evening"],
    },
    {
        "product_name": "Amber Bliss",
        "scent_family": ["Amber", "Oriental"],
        "scent_notes": ["Amber", "vanilla", "sweet", "warm", "resinous"],
        "intensity": "moderate",
        "longevity": "Long lasting",
        "occasion": ["Evening", "Daily"],
        "season": ["Winter", "All season"],
        "product_id": "amber_bliss",
        "target_audience": "Unisex",
        "price_min": 420,
        "available_sizes": ["6ml", "12ml"],
        "description": "Sweet amber resin with vanilla undertones. Warm and enveloping.",
        "tags": ["amber", "vanilla", "warm", "sweet", "evening"],
    },
    {
        "product_name": "Lavender Cool",
        "scent_family": ["Fresh", "Aromatic"],
        "scent_notes": ["Lavender", "fresh", "calming", "aromatic"],
        "intensity": "light",
        "longevity": "Moderate",
        "occasion": ["Daily", "Office"],
        "season": ["Spring", "Summer"],
        "product_id": "lavender_cool",
        "target_audience": "Unisex",
        "price_min": 390,
        "available_sizes": ["6ml", "12ml"],
        "description": "Fresh French lavender — calming, aromatic, and perfect for the office.",
        "tags": ["lavender", "fresh", "calming", "office", "daily"],
    },
]

MAX_RECOMMENDATIONS = 3

# Upper bound on catalog size — guards against accidentally loading a huge
# dataset into the in-memory recommendation path.
MAX_CATALOG_SIZE = 1000


def _validate_catalog(catalog: list[dict[str, Any]]) -> None:
    """
    Validate the in-memory catalog at import time.

    Raises ValueError if:
      - any product is missing a non-empty ``product_id``
      - any ``product_id`` is duplicated
      - the catalog exceeds ``MAX_CATALOG_SIZE``
    """
    if len(catalog) > MAX_CATALOG_SIZE:
        raise ValueError(
            f"Catalog size {len(catalog)} exceeds maximum of {MAX_CATALOG_SIZE}."
        )

    seen: set[str] = set()
    duplicates: set[str] = set()
    for product in catalog:
        product_id = product.get("product_id")
        if product_id is None or str(product_id).strip() == "":
            raise ValueError("Every catalog product must have a non-empty 'product_id'.")
        key = str(product_id).strip()
        if key in seen:
            duplicates.add(key)
        else:
            seen.add(key)

    if duplicates:
        raise ValueError(
            "Duplicate product_id(s) in catalog: " + ", ".join(sorted(duplicates))
        )


_validate_catalog(CATALOG)


def _normalize_list(val: list[str] | None) -> list[str]:
    if not val:
        return []
    return [v.strip().lower() for v in val if v]


def _match_score(
    product: dict[str, Any],
    scent_family: list[str] | None,
    intensity: str | None,
    occasion: list[str] | None,
    preferred_notes: list[str] | None,
) -> int:
    score = 0

    p_scent_fam = _normalize_list(product.get("scent_family"))
    p_notes = _normalize_list(product.get("scent_notes"))
    p_occasion = _normalize_list(product.get("occasion"))
    p_intensity = product.get("intensity", "").lower()
    p_season = _normalize_list(product.get("season"))

    q_scent_fam = _normalize_list(scent_family)
    q_occasion = _normalize_list(occasion)
    q_notes = _normalize_list(preferred_notes)
    q_intensity = (intensity or "").strip().lower()

    for q in q_scent_fam:
        if q in p_scent_fam:
            score += 5

    for q in q_notes:
        if q in p_notes:
            score += 3

    for q in q_occasion:
        if q in p_occasion:
            score += 3

    if q_intensity and q_intensity == p_intensity:
        score += 2

    return score


def recommend_products(
    budget: float | None = None,
    scent_family: list[str] | None = None,
    intensity: str | None = None,
    occasion: list[str] | None = None,
    preferred_notes: list[str] | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """
    Recommend products based on customer preferences.

    Parameters
    ----------
    budget : float | None
        Maximum budget in INR.
    scent_family : list[str] | None
        Desired scent families (e.g., ["Woody", "Oud"]).
    intensity : str | None
        Desired intensity: "light", "moderate", or "strong".
    occasion : list[str] | None
        Desired occasions (e.g., ["Evening", "Daily"]).
    preferred_notes : list[str] | None
        Preferred scent notes (e.g., ["Oud", "Sandalwood"]).
    limit : int
        Maximum number of recommendations to return (default 3).

    Returns
    -------
    list[dict]
        List of recommended products with matched_attributes, price_min,
        available_sizes, and reason.
    """
    # Enforce the maximum recommendation cap so callers never receive
    # more than MAX_RECOMMENDATIONS products, regardless of the requested limit.
    limit = min(limit, MAX_RECOMMENDATIONS)

    candidates = []

    has_preferences = any([
        scent_family,
        intensity,
        occasion,
        preferred_notes,
    ])

    for product in CATALOG:
        price_min = product.get("price_min", 0)

        if budget is not None and price_min > budget:
            continue

        score = _match_score(product, scent_family, intensity, occasion, preferred_notes)

        if has_preferences and score == 0:
            continue

        matched_attrs = []
        p_scent_fam = _normalize_list(product.get("scent_family"))
        p_notes = _normalize_list(product.get("scent_notes"))
        p_occasion = _normalize_list(product.get("occasion"))
        p_intensity = product.get("intensity", "").lower()

        q_scent_fam = _normalize_list(scent_family)
        q_occasion = _normalize_list(occasion)
        q_notes = _normalize_list(preferred_notes)
        q_intensity = (intensity or "").strip().lower()

        for q in q_scent_fam:
            if q in p_scent_fam:
                matched_attrs.append(q)
        for q in q_notes:
            if q in p_notes:
                matched_attrs.append(q)
        for q in q_occasion:
            if q in p_occasion:
                matched_attrs.append(q)
        if q_intensity and q_intensity == p_intensity:
            matched_attrs.append(q_intensity)

        matched_attrs = list(dict.fromkeys(matched_attrs))

        reason_parts = []
        if matched_attrs:
            reason_parts.append(f"Matches your preference for {', '.join(matched_attrs)}.")
        else:
            reason_parts.append("A good alternative based on available products.")

        candidates.append(
            {
                "product_name": product["product_name"],
                "matched_attributes": matched_attrs,
                "price_min": price_min,
                "available_sizes": product["available_sizes"],
                "description": product["description"],
                "reason": " ".join(reason_parts),
                "_score": score,
            }
        )

    candidates.sort(key=lambda x: (-x["_score"], x["price_min"]))

    results = []
    for c in candidates[:limit]:
        result = {k: v for k, v in c.items() if k != "_score"}
        results.append(result)

    return results


if __name__ == "__main__":
    import sys

    print("=== Recommendation Engine Demo ===\n")

    test_cases = [
        {"budget": 300, "scent_family": ["Woody"], "intensity": "strong"},
        {"budget": 500, "intensity": "strong"},
        {"scent_family": ["Woody"]},
        {"budget": 1000, "scent_family": ["Oud"], "occasion": ["Evening"]},
        {"preferred_notes": ["Rose", "Floral"]},
        {"budget": 400, "occasion": ["Daily", "Office"]},
    ]

    for i, tc in enumerate(test_cases, 1):
        print(f"Test {i}: {tc}")
        results = recommend_products(**tc, limit=3)
        for r in results:
            print(
                f"  - {r['product_name']} (Rs{r['price_min']}+) | "
                f"Attrs: {r['matched_attributes']} | {r['reason']}"
            )
        print()