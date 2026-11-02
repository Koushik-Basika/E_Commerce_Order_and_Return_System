"""
E-Commerce Order and Return System — Comprehensive Automated Verification Suite
Tests database schema, seeding, authentication, pagination, orders, 7-stage return workflow, refunds, reviews, and admin reports.
"""

import database
from database.connection import get_connection
from utils.auth import hash_password, verify_password
from utils.helpers import money, stars, format_date, get_status_badge
from database.repository import (
    authenticate_user,
    create_user,
    get_products_paginated,
    get_product_by_id,
    get_curated_products,
    get_categories,
    validate_coupon,
    create_order,
    get_user_orders,
    cancel_order,
    get_returnable_items_for_user,
    create_return_request,
    get_user_returns,
    get_user_refunds,
    update_order_status_admin,
    update_return_status_admin,
    add_product_review,
    get_product_reviews,
    get_product_rating_breakdown,
    get_admin_dashboard_kpis,
    get_admin_sales_chart_data,
    get_admin_return_reasons_data,
    get_report_data,
    toggle_wishlist,
    get_user_wishlist_ids
)

def run_all_tests():
    print("==================================================")
    print("RUNNING AUTOMATED TEST SUITE: E-Commerce Order and Return System")
    print("==================================================")

    # 1. Database Initialization & Seeding
    database.create_schema()
    database.seed_database(force_reseed=True)
    with database.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        assert count >= 700, f"Expected >= 700 products, got {count}"
        print(f"[PASS] 1. Database Schema & Seeding Verified: {count} realistic products in catalogue.")

    # 2. Authentication Test
    admin = authenticate_user("admin@example.com", "Admin@123")
    assert admin is not None and admin["role"] == "admin", "Admin authentication failed!"
    cust = authenticate_user("rahul.sharma@example.com", "Customer@123")
    assert cust is not None and cust["role"] == "customer", "Customer authentication failed!"
    bad = authenticate_user("admin@example.com", "WrongPassword")
    assert bad is None, "Security check failed: bad password allowed!"
    print("[PASS] 2. Authentication & PBKDF2 Password Verification Passed.")

    # 3. Product Catalogue & Pagination Test
    res = get_products_paginated(search="", page=1, per_page=24)
    assert len(res["items"]) == 24, f"Expected 24 items on page 1, got {len(res['items'])}"
    assert res["total_count"] >= 700, f"Expected total_count >= 700, got {res['total_count']}"
    assert res["total_pages"] >= 30, f"Expected >= 30 pages, got {res['total_pages']}"
    print(f"[PASS] 3. Pagination Verified: Showing {len(res['items'])} items of {res['total_count']} (Total Pages: {res['total_pages']}).")

    # 4. Search and Filter Tests
    search_res = get_products_paginated(search="Headphones", page=1, per_page=24)
    assert len(search_res["items"]) > 0, "Search for 'Headphones' returned 0 results"
    cat_res = get_products_paginated(category="Electronics", page=1, per_page=24)
    assert len(cat_res["items"]) > 0, "Category filter for 'Electronics' returned 0 results"
    for it in cat_res["items"]:
        assert it["category"] == "Electronics", f"Unexpected category {it['category']}"
    print(f"[PASS] 4. Search & Multi-Filter Query Tests Passed ({len(search_res['items'])} search hits, {len(cat_res['items'])} category hits).")

    # 5. Coupon Engine Test
    c_res = validate_coupon("WELCOME10", 2000.0)
    assert c_res["valid"] is True, "Coupon WELCOME10 validation failed"
    assert c_res["discount"] == 200.0, f"Expected 200.0 discount, got {c_res['discount']}"
    bad_c = validate_coupon("INVALID_CODE", 2000.0)
    assert bad_c["valid"] is False, "Invalid coupon passed"
    print(f"[PASS] 5. Coupon Engine Verified: Applied discount {c_res['discount']}.")

    # 6. Wishlist Toggle Test
    is_w = toggle_wishlist(cust["id"], res["items"][0]["id"])
    w_ids = get_user_wishlist_ids(cust["id"])
    assert res["items"][0]["id"] in w_ids, "Wishlist toggle add failed"
    # toggle off
    toggle_wishlist(cust["id"], res["items"][0]["id"])
    w_ids2 = get_user_wishlist_ids(cust["id"])
    assert res["items"][0]["id"] not in w_ids2, "Wishlist toggle remove failed"
    print("[PASS] 6. Wishlist Management Verified.")

    # 7. Order Placement & Stock Reduction Test
    test_prod = res["items"][1]
    stock_before = test_prod["stock"]
    cart_dict = {test_prod["id"]: 2}
    ok, msg, ord_num = create_order(
        user_id=cust["id"],
        cart_dict=cart_dict,
        shipping_address="Test Address, Bangalore",
        delivery_method="Express",
        payment_method="UPI",
        coupon_code="WELCOME10",
        discount=100.0
    )
    assert ok is True, f"Order placement failed: {msg}"
    prod_after = get_product_by_id(test_prod["id"])
    assert prod_after["stock"] == stock_before - 2, f"Stock not reduced properly: before={stock_before}, after={prod_after['stock']}"
    print(f"[PASS] 7. Order Placement & Stock Reduction Verified: Order #{ord_num} created.")

    # 8. Order Cancellation Test
    orders = get_user_orders(cust["id"])
    latest_order = orders[0]
    ok_cancel, msg_cancel = cancel_order(latest_order["id"], cust["id"], "Test cancellation")
    assert ok_cancel is True, f"Order cancellation failed: {msg_cancel}"
    prod_restored = get_product_by_id(test_prod["id"])
    assert prod_restored["stock"] == stock_before, "Stock was not restored upon cancellation"
    print("[PASS] 8. Order Cancellation & Stock Restoration Verified.")

    # 9. Returns & 7-Stage Workflow Test (CORE FEATURE)
    # Ensure product has guaranteed stock and place an isolated dedicated order
    ret_prod = res["items"][2]
    with get_connection() as c:
        c.execute("UPDATE products SET stock = stock + 10 WHERE id = ?", (ret_prod["id"],))

    ok_d, msg_d, d_ord_num = create_order(
        user_id=cust["id"],
        cart_dict={ret_prod["id"]: 2},
        shipping_address="Test Address, Bangalore",
        delivery_method="Express",
        payment_method="UPI"
    )
    assert ok_d is True, f"Failed placing return test order: {msg_d}"

    fresh_orders = get_user_orders(cust["id"])
    target_order = next((o for o in fresh_orders if o["order_number"] == d_ord_num), None)
    assert target_order is not None, f"Order {d_ord_num} not found in user orders"

    # Step through fulfillment to Delivered
    for stg in ["Confirmed", "Packed", "Shipped", "Out for Delivery", "Delivered"]:
        ok_step, msg_step = update_order_status_admin(target_order["id"], stg)
        assert ok_step is True, f"Failed advancing order status to {stg}: {msg_step}"

    # Verify returnable items for this delivered order
    ret_items = [it for it in get_returnable_items_for_user(cust["id"]) if it["order_id"] == target_order["id"]]
    assert len(ret_items) > 0, "No returnable items found for delivered order"
    target_item = ret_items[0]
    ok_ret, msg_ret = create_return_request(
        order_id=target_item["order_id"],
        order_item_id=target_item["id"],
        product_id=target_item["product_id"],
        user_id=cust["id"],
        quantity=1,
        reason="Defective",
        comments="Sound distortion in right ear",
        refund_method="UPI"
    )
    assert ok_ret is True, f"Return filing failed: {msg_ret}"

    # Advance return through 7-stage workflow
    user_returns = get_user_returns(cust["id"])
    latest_ret = user_returns[0]
    stages = [
        "Under Review",
        "Approved",
        "Pickup Scheduled",
        "Product Received",
        "Refund Initiated",
        "Refund Completed"
    ]
    for stage in stages:
        ok_adv, msg_adv = update_return_status_admin(latest_ret["id"], stage, f"Test note for {stage}")
        assert ok_adv is True, f"Failed advancing to {stage}: {msg_adv}"

    # Verify refund created and completed
    refunds = get_user_refunds(cust["id"])
    assert len(refunds) > 0, "No refund records generated!"
    assert refunds[0]["status"] == "Completed", f"Expected Completed refund, got {refunds[0]['status']}"
    print(f"[PASS] 9. CORE FEATURE: 7-Stage Return Workflow & Refund Execution Passed (Refund #{refunds[0]['refund_number']}).")

    # 10. Reviews & Ratings Breakdown Test
    add_product_review(
        product_id=test_prod["id"],
        user_id=cust["id"],
        user_name=cust["name"],
        rating=5,
        headline="Awesome sound quality",
        comment="Exceeded all expectations. Would buy again!"
    )
    revs = get_product_reviews(test_prod["id"])
    assert len(revs) > 0, "Review not saved"
    r_stats = get_product_rating_breakdown(test_prod["id"])
    assert r_stats["total_reviews"] > 0, "Review breakdown total is 0"
    print("[PASS] 10. Product Reviews & Rating Distribution Verified.")

    # 11. Admin KPIs, Analytics & Data Export Test
    kpis = get_admin_dashboard_kpis()
    assert kpis["products_count"] >= 700, "KPI product count mismatch"
    assert kpis["orders_count"] > 0, "KPI orders count is 0"
    sales_chart = get_admin_sales_chart_data()
    assert isinstance(sales_chart, list), "Sales chart data format invalid"
    rep_sales = get_report_data("sales")
    assert len(rep_sales) > 0, "Sales report export empty"
    rep_ret = get_report_data("returns")
    assert len(rep_ret) > 0, "Returns report export empty"
    print("[PASS] 11. Admin KPIs, Analytics & CSV Report Data Generation Verified.")

    print("==================================================")
    print("ALL 11 TEST SUITES PASSED SUCCESSFULLY (100% PASS RATE)")
    print("==================================================")

if __name__ == "__main__":
    run_all_tests()
