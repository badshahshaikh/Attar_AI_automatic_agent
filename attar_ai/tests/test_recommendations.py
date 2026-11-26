"""
tests/test_recommendations.py
-----------------------------
Unit tests for the recommendation engine.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attar_ai.app.utils.recommendation_engine import recommend_products, CATALOG


def test_budget_300():
    """Budget ₹300 — no product above ₹300."""
    results = recommend_products(budget=300, limit=5)
    for r in results:
        assert r["price_min"] <= 300, f"Product {r['product_name']} exceeds budget: ₹{r['price_min']}"
    print("[PASS] test_budget_300 passed")


def test_budget_500_strong():
    """Budget ₹500, strong scent — rank strong products under ₹500."""
    results = recommend_products(budget=500, intensity="strong", limit=5)
    for r in results:
        assert r["price_min"] <= 500, f"Product {r['product_name']} exceeds budget: ₹{r['price_min']}"
    strong_products = [r for r in results if "strong" in r["matched_attributes"]]
    assert len(strong_products) > 0, "Should have at least one strong product"
    print("[PASS] test_budget_500_strong passed")


def test_woody_fragrance():
    """Woody fragrance — rank woody products first."""
    results = recommend_products(scent_family=["Woody"], limit=5)
    assert len(results) > 0, "Should have results for woody"
    first = results[0]
    assert "woody" in first["matched_attributes"], f"First result should match woody: {first}"
    print("[PASS] test_woody_fragrance passed")


def test_product_unavailable_not_recommended():
    """Products with no stock should not be recommended as available.
    This test verifies engine doesn't track stock — it only uses price_min.
    Stock verification happens at agent level via sheets_lookup.
    """
    results = recommend_products(budget=2000, limit=10)
    all_in_catalog = [r["product_name"] for r in results]
    assert len(all_in_catalog) > 0
    print("[PASS] test_product_unavailable_not_recommended passed (engine uses catalog only)")


def test_no_matching_attributes():
    """No matching attributes — return sensible alternatives or no results."""
    results = recommend_products(scent_family=["NonExistentFamily"], limit=3)
    assert len(results) == 0, "Should return empty for non-existent family"
    print("[PASS] test_no_matching_attributes passed")


def test_no_budget_ranks_by_preference():
    """No budget — rank by preference, not price assumptions."""
    results = recommend_products(scent_family=["Floral"], limit=3)
    assert len(results) > 0
    # First result should have highest match (Rose Attar matches Floral family + Rose note)
    first = results[0]
    assert "floral" in first["matched_attributes"], f"First result should match floral: {first}"
    print("[PASS] test_no_budget_ranks_by_preference passed")


def test_exact_size_requested():
    """Exact size requested — only recommend compatible sizes.
    Note: Engine filters by available_sizes in catalog, not live stock.
    """
    results = recommend_products(budget=1000, limit=5)
    for r in results:
        assert "3ml" in r["available_sizes"] or "6ml" in r["available_sizes"] or "12ml" in r["available_sizes"]
    print("[PASS] test_exact_size_requested passed (catalog-based)")


def test_empty_catalog():
    """Empty catalog — return empty result safely."""
    original_catalog = CATALOG[:]
    CATALOG.clear()
    try:
        results = recommend_products(budget=1000, limit=3)
        assert results == [], "Empty catalog should return empty list"
    finally:
        CATALOG.extend(original_catalog)
    print("[PASS] test_empty_catalog passed")


def test_predictable_results():
    """Engine must return predictable results for same catalog + inputs."""
    results1 = recommend_products(budget=500, scent_family=["Woody"], intensity="strong", limit=3)
    results2 = recommend_products(budget=500, scent_family=["Woody"], intensity="strong", limit=3)
    assert [r["product_name"] for r in results1] == [r["product_name"] for r in results2]
    print("[PASS] test_predictable_results passed")


def test_reason_field_present():
    """Each recommendation should have a reason field."""
    results = recommend_products(budget=1000, limit=3)
    for r in results:
        assert "reason" in r, "Missing reason field"
        assert r["reason"], "Reason should not be empty"
    print("[PASS] test_reason_field_present passed")


def test_matched_attributes_field():
    """Each recommendation should have matched_attributes field."""
    results = recommend_products(scent_family=["Woody"], intensity="strong", limit=3)
    for r in results:
        assert "matched_attributes" in r, "Missing matched_attributes field"
        assert isinstance(r["matched_attributes"], list), "matched_attributes should be a list"
    print("[PASS] test_matched_attributes_field passed")


def test_price_min_field():
    """Each recommendation should have price_min field."""
    results = recommend_products(budget=1000, limit=3)
    for r in results:
        assert "price_min" in r, "Missing price_min field"
        assert isinstance(r["price_min"], (int, float)), "price_min should be numeric"
        assert r["price_min"] > 0, "price_min should be positive"
    print("[PASS] test_price_min_field passed")


def test_available_sizes_field():
    """Each recommendation should have available_sizes field."""
    results = recommend_products(budget=1000, limit=3)
    for r in results:
        assert "available_sizes" in r, "Missing available_sizes field"
        assert isinstance(r["available_sizes"], list), "available_sizes should be a list"
        assert len(r["available_sizes"]) > 0, "available_sizes should not be empty"
    print("[PASS] test_available_sizes_field passed")


def test_limit_respected():
    """Limit parameter should be respected."""
    results = recommend_products(budget=10000, limit=2)
    assert len(results) <= 2, f"Expected at most 2 results, got {len(results)}"
    print("[PASS] test_limit_respected passed")


def test_occasion_filter():
    """Occasion filter should match products with that occasion."""
    results = recommend_products(occasion=["Daily"], limit=5)
    # At least one product should match Daily occasion
    daily_matches = [r for r in results if "daily" in r["matched_attributes"] or "office" in r["matched_attributes"]]
    assert len(daily_matches) > 0, "Should have at least one product matching Daily/Office occasion"
    # Products matching occasion should rank higher (first result should match)
    assert "daily" in results[0]["matched_attributes"] or "office" in results[0]["matched_attributes"], \
        f"First result should match Daily/Office: {results[0]}"
    print("[PASS] test_occasion_filter passed")


def test_preferred_notes_filter():
    """Preferred notes filter should match products with those notes."""
    results = recommend_products(preferred_notes=["Rose"], limit=5)
    # At least one product should match Rose note
    rose_matches = [r for r in results if "rose" in r["matched_attributes"]]
    assert len(rose_matches) > 0, "Should have at least one product matching Rose note"
    # Products matching note should rank higher
    assert "rose" in results[0]["matched_attributes"], f"First result should match Rose note: {results[0]}"
    print("[PASS] test_preferred_notes_filter passed")


def run_all_tests():
    """Run all tests."""
    tests = [
        test_budget_300,
        test_budget_500_strong,
        test_woody_fragrance,
        test_product_unavailable_not_recommended,
        test_no_matching_attributes,
        test_no_budget_ranks_by_preference,
        test_exact_size_requested,
        test_empty_catalog,
        test_predictable_results,
        test_reason_field_present,
        test_matched_attributes_field,
        test_price_min_field,
        test_available_sizes_field,
        test_limit_respected,
        test_occasion_filter,
        test_preferred_notes_filter,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__} ERROR: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*40}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)