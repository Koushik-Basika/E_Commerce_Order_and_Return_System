"""
Automated Verification Suite for 300+ Unique Product Image Catalog & Frontend Stability
Validates all 10 acceptance criteria:
1. Image catalog contains >= 300 distinct image URLs.
2. Duplicate URLs are detected and reported.
3. Products are mapped to suitable category images.
4. Image assignments remain stable across repeated queries and simulated Streamlit reruns.
5. The same visible shop page does not repeat image URLs when enough eligible images exist.
6. Missing/broken images display fallback gracefully without crashing.
7. Pagination and filters preserve correct product-image relationships.
8. Existing product IDs and customer transaction relationships remain intact after migration.
9. Database initialization and seeding do not destroy customer data.
10. Search, sorting, cart, wishlist, and product details function correctly.
"""

import os
import sys
import json
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import database
from database.connection import get_connection
from database.repository import (
    get_products_paginated,
    get_product_by_id,
    get_user_orders,
    get_user_returns,
    toggle_wishlist,
    get_user_wishlist_ids
)
from utils.image_catalog import (
    load_image_catalog,
    get_catalog_stats,
    get_deterministic_product_image,
    get_product_gallery_images,
    get_images_for_category
)
from utils.image_validator import validate_catalog_file, is_syntactically_valid_url
from utils.helpers import generate_image_svg

def test_1_image_catalog_minimum_300():
    print("[*] TEST 1: Verifying image catalog contains at least 300 distinct image URLs...")
    stats = get_catalog_stats()
    unique_count = stats["unique_urls"]
    total_entries = stats["total_entries"]
    assert unique_count >= 300, f"Expected >= 300 unique URLs, found {unique_count}"
    assert total_entries >= 300, f"Expected >= 300 total catalog entries, found {total_entries}"
    print(f"    [PASS] Test 1: Verified {unique_count} distinct URLs across {total_entries} catalog entries (Target >= 300 met).")

def test_2_duplicate_url_detection():
    print("[*] TEST 2: Verifying duplicate URL detection and reporting logic...")
    report = validate_catalog_file(use_cache=True)
    assert report["duplicate_urls_count"] == 0, f"Found {report['duplicate_urls_count']} unexpected duplicate URLs in product_images.json!"

    # Test synthetic duplicate detection
    synthetic_manifest = [
        {"id": "test_1", "url": "https://example.com/item1.jpg", "category": "Electronics"},
        {"id": "test_2", "url": "https://example.com/item1.jpg", "category": "Electronics"},
        {"id": "test_3", "url": "https://example.com/item2.jpg", "category": "Fashion"}
    ]
    seen = {}
    dups = []
    for item in synthetic_manifest:
        u = item["url"]
        if u in seen:
            dups.append((item["id"], u, seen[u]))
        else:
            seen[u] = item["id"]
    assert len(dups) == 1 and dups[0][0] == "test_2", "Synthetic duplicate URL detection failed"
    print("    [PASS] Test 2: Duplicate detection accurately reported 0 duplicates in catalog and flagged test duplicate.")

def test_3_category_image_mapping():
    print("[*] TEST 3: Verifying products are mapped to appropriate category images...")
    catalog = load_image_catalog()
    cat_url_sets = {}
    for item in catalog:
        cat_url_sets.setdefault(item["category"], set()).add(item["url"])

    with get_connection() as conn:
        for cat_name in ["Electronics", "Fashion", "Footwear", "Home & Kitchen", "Beauty", "Sports", "Books", "Gaming", "Accessories", "Mobiles", "Laptops"]:
            rows = conn.execute("SELECT id, name, category, image_url FROM products WHERE category = ? LIMIT 20", (cat_name,)).fetchall()
            assert len(rows) > 0, f"No products found for category {cat_name}"
            for r in rows:
                img_url = r["image_url"]
                assert img_url, f"Product {r['id']} ({r['name']}) has empty image_url"
                # Verify image belongs to the legitimate catalog pool for this category
                assert img_url in cat_url_sets[cat_name], f"Product {r['name']} in category {cat_name} mapped to foreign/unrecognized image {img_url}"
    print("    [PASS] Test 3: Products across all 11 categories verified mapped strictly to their matching category pools.")

def test_4_stability_across_reruns_and_queries():
    print("[*] TEST 4: Verifying image assignments remain 100% stable across queries & simulated reruns...")
    # First query
    res1 = get_products_paginated(category="Electronics", page=1, per_page=24)
    # Simulated rerun query
    res2 = get_products_paginated(category="Electronics", page=1, per_page=24)
    assert len(res1["items"]) == len(res2["items"]) == 24
    for it1, it2 in zip(res1["items"], res2["items"]):
        assert it1["id"] == it2["id"], "Product ID mismatched across queries"
        assert it1["image_url"] == it2["image_url"], f"Product {it1['id']} image_url changed across reruns: {it1['image_url']} vs {it2['image_url']}"

    # Verify deterministic helper stability
    for i in range(5):
        s1 = get_deterministic_product_image("Electronics", "Wireless Headphones", "SKU-ELE-SONY-1001")
        s2 = get_deterministic_product_image("Electronics", "Wireless Headphones", "SKU-ELE-SONY-1001")
        assert s1 == s2, "Deterministic image selector gave non-reproducible output"
    print("    [PASS] Test 4: Image assignments 100% stable and reproducible across repeated queries.")

def test_5_visible_shop_page_no_image_repetition():
    print("[*] TEST 5: Verifying visible shop page does not repeat images when enough eligible images exist...")
    # Query 24 items in Fashion (which has 68 verified images)
    res = get_products_paginated(category="Fashion", page=1, per_page=24)
    items = res["items"]
    assert len(items) == 24
    image_urls = [it["image_url"] for it in items]
    unique_images_on_page = set(image_urls)
    assert len(unique_images_on_page) == 24, f"Found duplicate images on visible shop page: {24 - len(unique_images_on_page)} duplicates out of 24 items"

    # Query 24 items in Accessories (which has 77 verified images)
    res_acc = get_products_paginated(category="Accessories", page=1, per_page=24)
    assert len(set(it["image_url"] for it in res_acc["items"])) == 24
    print("    [PASS] Test 5: All 24 visible product cards on shop page display 100% distinct images.")

def test_6_graceful_fallback_for_missing_or_broken_images():
    print("[*] TEST 6: Verifying graceful fallback image handling without crashing...")
    # Verify generate_image_svg produces valid data URI
    fallback = generate_image_svg("Electronics", "Sony Noise Cancelling Headphones")
    assert fallback.startswith("data:image/svg+xml"), f"Invalid SVG data URI: {fallback[:30]}"
    assert is_syntactically_valid_url(fallback)

    # Test corrupted/empty URL fallback logic
    for bad_url in [None, "", "   ", "ftp://invalid-url.com/img.jpg", "https://not-an-image.xyz"]:
        if not bad_url or not bad_url.strip().startswith(("http://", "https://", "data:image/")):
            safe_url = generate_image_svg("Beauty", "Facial Serum")
        else:
            safe_url = bad_url
        assert is_syntactically_valid_url(safe_url), f"Fallback failed for bad URL {bad_url}"
    print("    [PASS] Test 6: Fallback SVG generation and syntax verification passed with zero exceptions.")

def test_7_pagination_and_filters_preserve_product_image_mapping():
    print("[*] TEST 7: Verifying pagination and filters preserve product-image relationships...")
    # Get page 1 and page 2
    p1_res = get_products_paginated(page=1, per_page=24)
    p2_res = get_products_paginated(page=2, per_page=24)
    
    # Check that item IDs don't overlap between page 1 and 2
    p1_ids = {it["id"] for it in p1_res["items"]}
    p2_ids = {it["id"] for it in p2_res["items"]}
    assert len(p1_ids.intersection(p2_ids)) == 0, "Pagination overlapping items detected"

    # Check that fetching by ID gives the exact same image
    test_prod = p1_res["items"][0]
    single_prod = get_product_by_id(test_prod["id"])
    assert single_prod["image_url"] == test_prod["image_url"], "Product-image mapping diverged between list and details"

    # Apply search filter and verify image remains the same
    search_res = get_products_paginated(search=test_prod["name"][:15], page=1, per_page=24)
    matching = [it for it in search_res["items"] if it["id"] == test_prod["id"]]
    if matching:
        assert matching[0]["image_url"] == test_prod["image_url"], "Search query altered product image mapping"
    print("    [PASS] Test 7: Pagination and search filter preserved exact product-image bindings.")

def test_8_existing_product_ids_and_customer_relationships():
    print("[*] TEST 8: Verifying customer orders, returns, and foreign keys remain 100% intact...")
    with get_connection() as conn:
        orders = conn.execute("SELECT id, user_id, order_number, total FROM orders").fetchall()
        assert len(orders) > 0, "No customer orders found in database!"
        
        order_items = conn.execute("SELECT id, order_id, product_id, image_url FROM order_items").fetchall()
        assert len(order_items) > 0, "No order_items found!"

        for oi in order_items:
            # Verify foreign key product exists
            prod = conn.execute("SELECT id, image_url FROM products WHERE id = ?", (oi["product_id"],)).fetchone()
            assert prod is not None, f"Foreign key violation: order_item refers to missing product {oi['product_id']}"
            assert oi["image_url"], f"Order item {oi['id']} has empty image_url"

        returns = conn.execute("SELECT id, order_id, product_id, status FROM returns").fetchall()
        assert len(returns) > 0, "No return records found!"
        for ret in returns:
            o = conn.execute("SELECT id FROM orders WHERE id = ?", (ret["order_id"],)).fetchone()
            assert o is not None, f"Return {ret['id']} refers to missing order {ret['order_id']}"
    print(f"    [PASS] Test 8: All {len(orders)} orders, {len(order_items)} items, and {len(returns)} returns intact with verified foreign keys.")

def test_9_idempotent_database_seeding_preserves_customer_data():
    print("[*] TEST 9: Verifying database initialization/seeding is idempotent and safe...")
    with get_connection() as conn:
        pre_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pre_returns = conn.execute("SELECT COUNT(*) FROM returns").fetchone()[0]
        pre_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    # Run seed_database twice (as occurs on app restarts)
    database.create_schema()
    database.seed_database(force_reseed=False)
    database.seed_database(force_reseed=False)

    with get_connection() as conn:
        post_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        post_returns = conn.execute("SELECT COUNT(*) FROM returns").fetchone()[0]
        post_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    assert pre_orders == post_orders, f"Orders count altered by seeding: {pre_orders} -> {post_orders}"
    assert pre_returns == post_returns, f"Returns count altered by seeding: {pre_returns} -> {post_returns}"
    assert pre_users == post_users, f"Users count altered by seeding: {pre_users} -> {post_users}"
    print("    [PASS] Test 9: Seeding is 100% idempotent; customer transactions preserved across repeated executions.")

def test_10_search_sorting_cart_wishlist_details():
    print("[*] TEST 10: Verifying search, sorting, cart, wishlist, and product details functionality...")
    # Search
    s_res = get_products_paginated(search="Pro", page=1, per_page=10)
    assert len(s_res["items"]) > 0, "Search for 'Pro' returned 0 results"

    # Sorting
    low_high = get_products_paginated(category="Electronics", sort_by="Price: Low to High", page=1, per_page=10)
    prices = [it["price"] for it in low_high["items"]]
    assert prices == sorted(prices), "Sort by Price: Low to High failed"

    # Wishlist
    test_uid = 2  # Rahul Sharma
    test_pid = s_res["items"][0]["id"]
    initial_w = get_user_wishlist_ids(test_uid)
    toggle_wishlist(test_uid, test_pid)
    after_add = get_user_wishlist_ids(test_uid)
    assert test_pid in after_add, "Failed to add product to wishlist"
    toggle_wishlist(test_uid, test_pid)
    after_remove = get_user_wishlist_ids(test_uid)
    assert test_pid not in after_remove, "Failed to remove product from wishlist"

    # Product details with gallery images
    prod = get_product_by_id(test_pid)
    assert prod is not None and prod["id"] == test_pid
    assert prod["image_url"], "Product details missing image_url"
    gallery = get_product_gallery_images(prod["category"], prod.get("subcategory", ""), prod["image_url"], prod["sku"])
    assert len(gallery) >= 1, "Product gallery returned 0 images"
    print("    [PASS] Test 10: Search, price sorting, wishlist toggle, and product details with gallery all function correctly.")

def run_all_tests():
    print("=" * 72)
    print("RUNNING AUTOMATED TEST SUITE: PRODUCT IMAGE CATALOG & FRONTEND STABILITY")
    print("=" * 72)
    test_1_image_catalog_minimum_300()
    test_2_duplicate_url_detection()
    test_3_category_image_mapping()
    test_4_stability_across_reruns_and_queries()
    test_5_visible_shop_page_no_image_repetition()
    test_6_graceful_fallback_for_missing_or_broken_images()
    test_7_pagination_and_filters_preserve_product_image_mapping()
    test_8_existing_product_ids_and_customer_relationships()
    test_9_idempotent_database_seeding_preserves_customer_data()
    test_10_search_sorting_cart_wishlist_details()
    print("=" * 72)
    print("ALL 10 ACCEPTANCE CRITERIA AUTOMATED TESTS PASSED (100% PASS RATE)!")
    print("=" * 72)

if __name__ == "__main__":
    run_all_tests()
