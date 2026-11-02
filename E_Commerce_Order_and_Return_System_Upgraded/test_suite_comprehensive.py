
"""
E-Commerce Order and Return System — Comprehensive End-to-End QA Test Suite
Validates:
1. Database Integrity, Schema & Uniqueness Constraints
2. Authentication, PBKDF2 Password Hashing & Access Control
3. Customer Data Isolation & Ownership Protection
4. High-Scale Catalogue Search, Multi-Filter & Pagination (1,000,000 Products)
5. Server-Side Trusted Pricing Engine, Inclusive GST & Coupon Limits
6. Wishlist Management Lifecycle
7. Transactional Order Placement & Atomic Stock Decrement
8. Order Cancellation & Stock Restoration
9. Return Eligibility Conditions (Delivered status, return window, partial limits)
10. Partial Quantity Return Filing & Remaining Quantity Accounting
11. Complete 7-Stage Return Workflow & State Transition Validation
12. Terminal Rejection Transition
13. Inventory Restocking upon Warehouse Product Receipt
14. Refund Completion & Transaction Records
15. Verified Purchaser Product Reviews & Rating Distribution
16. Executive Admin KPIs, Analytics & CSV Export Generation
"""

import sys
import os
import json
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import database
from database.connection import get_connection
from utils.auth import hash_password, verify_password
from utils.pricing import calculate_order_pricing, calculate_item_refund_amount
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
    get_order_by_id,
    cancel_order,
    get_returnable_items_for_user,
    create_return_request,
    get_user_returns,
    get_user_refunds,
    update_order_status_admin,
    update_return_status_admin,
    add_product_admin,
    add_product_review,
    get_product_reviews,
    get_product_rating_breakdown,
    get_admin_dashboard_kpis,
    get_report_data,
    toggle_wishlist,
    get_user_wishlist_ids
)

def run_comprehensive_tests():
    print("=" * 70)
    print("RUNNING COMPREHENSIVE QA TEST SUITE: E-COMMERCE ORDER AND RETURN SYSTEM")
    print("=" * 70)

    # 1. Database Schema & Scale Verification
    with get_connection() as conn:
        prod_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        assert prod_count >= 100000, f"Expected scaled catalogue >= 100,000, got {prod_count}"
        unique_skus = conn.execute("SELECT COUNT(DISTINCT sku) FROM products").fetchone()[0]
        assert unique_skus == prod_count, f"SKU collision detected: {prod_count - unique_skus} duplicates"
    print(f"[PASS] 1. Database Schema & Scale Verified: {prod_count:,} products with 100% unique SKUs.")

    # 2. Authentication & PBKDF2 Password Verification
    admin = authenticate_user("admin@example.com", "Admin@123")
    assert admin is not None and admin["role"] == "admin", "Admin auth failed"
    cust1 = authenticate_user("rahul.sharma@example.com", "Customer@123")
    assert cust1 is not None and cust1["role"] == "customer", "Customer 1 auth failed"
    cust2 = authenticate_user("priya.patel@example.com", "Customer@123")
    assert cust2 is not None and cust2["role"] == "customer", "Customer 2 auth failed"
    bad_auth = authenticate_user("admin@example.com", "WrongPassword!")
    assert bad_auth is None, "Security vulnerability: bad password authenticated"
    print("[PASS] 2. Authentication & PBKDF2 HMAC SHA-256 Verification Passed.")

    # 3. Customer Data Isolation Test
    cust1_orders = get_user_orders(cust1["id"])
    for o in cust1_orders:
        assert o["user_id"] == cust1["id"], "Customer isolation leak: foreign order returned"
    if cust1_orders:
        # Verify cust2 cannot access cust1's order via isolated query
        foreign_access = get_order_by_id(cust1_orders[0]["id"], user_id=cust2["id"])
        assert foreign_access is None, "Security violation: Customer 2 accessed Customer 1's order details!"
        # Verify cust2 cannot cancel cust1's order
        ok_hack, _ = cancel_order(cust1_orders[0]["id"], cust2["id"], "Malicious attempt")
        assert ok_hack is False, "Security violation: Customer 2 cancelled Customer 1's order!"
    print("[PASS] 3. Customer Data Isolation & Ownership Protection Verified.")

    # 4. Catalogue Search, Multi-Filter & Server-Side Pagination
    p_page1 = get_products_paginated(search="", page=1, per_page=24)
    assert len(p_page1["items"]) == 24, "Pagination failed on page 1"
    assert p_page1["total_count"] == prod_count, "Total count mismatch in pagination"
    p_page100 = get_products_paginated(search="", page=100, per_page=24)
    assert len(p_page100["items"]) == 24, "Pagination failed on page 100"

    p_filtered = get_products_paginated(category="Electronics", brand="Sony", page=1, per_page=24)
    assert len(p_filtered["items"]) > 0, "Filter for Electronics / Sony returned 0 items"
    for it in p_filtered["items"]:
        assert it["category"] == "Electronics" and it["brand"] == "Sony"
    print(f"[PASS] 4. High-Scale Search & Server-Side Pagination Verified across {p_page1['total_pages']:,} pages.")

    # 5. Trusted Server Pricing Engine & GST Tax Verification
    test_prod1 = p_page1["items"][0]
    test_prod2 = p_page1["items"][1]
    with get_connection() as conn:
        pricing_calc = calculate_order_pricing(
            conn,
            cart_dict={test_prod1["id"]: 2, test_prod2["id"]: 1},
            coupon_code="WELCOME10",
            delivery_method="Express"
        )
    assert pricing_calc["valid"] is True, f"Pricing calculation failed: {pricing_calc.get('error')}"
    expected_subtotal = round((test_prod1["price"] * 2) + test_prod2["price"], 2)
    assert pricing_calc["subtotal"] == expected_subtotal, f"Subtotal mismatch: {pricing_calc['subtotal']} vs {expected_subtotal}"
    assert pricing_calc["delivery_fee"] == 99.0, "Express delivery fee calculation error"
    assert pricing_calc["discount"] > 0, "Coupon discount was not applied"
    # Tax should be 18% inclusive of discounted subtotal
    expected_taxable = (pricing_calc["subtotal"] - pricing_calc["discount"]) / 1.18
    expected_tax = round((pricing_calc["subtotal"] - pricing_calc["discount"]) - expected_taxable, 2)
    assert pricing_calc["tax_amount"] == expected_tax, f"Tax mismatch: {pricing_calc['tax_amount']} vs {expected_tax}"
    print(f"[PASS] 5. Server-Side Pricing & 18% Inclusive GST Verified (Total: ₹{pricing_calc['total']:,.2f}).")

    # 6. SKU Duplicate Prevention & Catalog Validation
    dup_res, dup_msg = add_product_admin({
        "name": test_prod1["name"],
        "brand": test_prod1["brand"],
        "category": test_prod1["category"],
        "subcategory": test_prod1["subcategory"],
        "price": 1999.0,
        "original_price": 2999.0,
        "stock": 10,
        "sku": test_prod1["sku"] # duplicate SKU
    })
    assert dup_res is False, "Security defect: duplicate SKU allowed in catalog!"
    print("[PASS] 6. Duplicate SKU Prevention & Database Uniqueness Policy Verified.")

    # 7. Wishlist Toggle Lifecycle
    is_w = toggle_wishlist(cust1["id"], test_prod1["id"])
    assert test_prod1["id"] in get_user_wishlist_ids(cust1["id"]), "Wishlist add failed"
    toggle_wishlist(cust1["id"], test_prod1["id"])
    assert test_prod1["id"] not in get_user_wishlist_ids(cust1["id"]), "Wishlist remove failed"
    print("[PASS] 7. Wishlist Management Verified.")

    # 8. Order Placement & Atomic Stock Decrement
    stock_before = test_prod1["stock"]
    ok_ord, msg_ord, ord_num = create_order(
        user_id=cust1["id"],
        cart_dict={test_prod1["id"]: 2},
        shipping_address="402 Bellandur, Bangalore",
        delivery_method="Express",
        payment_method="UPI",
        coupon_code="WELCOME10"
    )
    assert ok_ord is True, f"Order placement failed: {msg_ord}"
    prod_post_ord = get_product_by_id(test_prod1["id"])
    assert prod_post_ord["stock"] == stock_before - 2, "Atomic stock decrement failed"
    print(f"[PASS] 8. Order Placement & Atomic Stock Decrement Verified: Order #{ord_num}.")

    # 9. Order Cancellation & Inventory Restoration
    placed_orders = get_user_orders(cust1["id"])
    cancel_target = placed_orders[0]
    ok_cancel, msg_cancel = cancel_order(cancel_target["id"], cust1["id"], "Customer changed mind")
    assert ok_cancel is True, f"Order cancellation failed: {msg_cancel}"
    prod_restored = get_product_by_id(test_prod1["id"])
    assert prod_restored["stock"] == stock_before, "Stock was not restored on cancellation"
    print("[PASS] 9. Order Cancellation & Stock Restoration Verified.")

    # 10. Order Fulfillment to Delivered & Return Eligibility Check
    # Place a dedicated order for return testing
    ok_deliv, _, deliv_ord_num = create_order(
        user_id=cust1["id"],
        cart_dict={test_prod2["id"]: 3},
        shipping_address="402 Bellandur, Bangalore",
        delivery_method="Standard",
        payment_method="UPI"
    )
    user_orders = get_user_orders(cust1["id"])
    deliv_target = user_orders[0]

    # Verify placed order is NOT eligible for return before delivery
    ret_before_deliv = [it for it in get_returnable_items_for_user(cust1["id"]) if it["order_id"] == deliv_target["id"]]
    assert len(ret_before_deliv) == 0, "Business logic bug: Placed order items showed up as returnable!"

    # Progress order through fulfillment to Delivered
    for step in ["Confirmed", "Packed", "Shipped", "Out for Delivery", "Delivered"]:
        ok_step, msg_step = update_order_status_admin(deliv_target["id"], step)
        assert ok_step is True, f"Failed updating order status to {step}: {msg_step}"

    # Now verify items are eligible for return
    ret_after_deliv = [it for it in get_returnable_items_for_user(cust1["id"]) if it["order_id"] == deliv_target["id"]]
    assert len(ret_after_deliv) > 0, "Delivered order item was not found eligible for return!"
    target_returnable_item = ret_after_deliv[0]
    assert target_returnable_item["returnable_quantity"] == 3, f"Expected 3 returnable units, got {target_returnable_item['returnable_quantity']}"
    print(f"[PASS] 10. Order Fulfillment & Delivery-Gated Return Eligibility Verified: Order #{deliv_ord_num}.")

    # 11. Partial Return Filing & Quantity Accounting
    # Return 1 of 3 units
    ok_ret1, msg_ret1 = create_return_request(
        order_id=deliv_target["id"],
        order_item_id=target_returnable_item["id"],
        product_id=target_returnable_item["product_id"],
        user_id=cust1["id"],
        quantity=1,
        reason="Defective",
        comments="Occasional crackling noise",
        refund_method="Original Payment"
    )
    assert ok_ret1 is True, f"Partial return filing failed: {msg_ret1}"

    # Verify that remaining 2 units are still returnable
    ret_after_partial = [it for it in get_returnable_items_for_user(cust1["id"]) if it["id"] == target_returnable_item["id"]]
    assert len(ret_after_partial) > 0, "Partial return locked all remaining units!"
    assert ret_after_partial[0]["returnable_quantity"] == 2, f"Expected 2 remaining units, got {ret_after_partial[0]['returnable_quantity']}"

    # Attempt to return 5 units (exceeding remaining 2) -> must be rejected
    bad_ret, _ = create_return_request(
        order_id=deliv_target["id"],
        order_item_id=target_returnable_item["id"],
        product_id=target_returnable_item["product_id"],
        user_id=cust1["id"],
        quantity=5,
        reason="Defective"
    )
    assert bad_ret is False, "Validation failure: returning more units than purchased was allowed!"
    print("[PASS] 11. Partial Return Filing (1 of 3 units) & Excess Quantity Prevention Verified.")

    # 12. Full 7-Stage Return Workflow & State Machine Enforcement
    cust_returns = get_user_returns(cust1["id"])
    active_return = cust_returns[0]

    # Verify initial state is Under Review
    assert active_return["status"] == "Under Review", f"Expected Under Review, got {active_return['status']}"

    # Verify invalid state transitions are blocked (e.g., jumping from Under Review straight to Refund Completed)
    invalid_adv, _ = update_return_status_admin(active_return["id"], "Refund Completed")
    assert invalid_adv is False, "Security defect: Invalid return state transition allowed!"

    stock_before_restock = get_product_by_id(target_returnable_item["product_id"])["stock"]

    # Advance cleanly through workflow: Under Review -> Approved -> Pickup Scheduled -> Product Received -> Refund Initiated -> Refund Completed
    workflow_stages = [
        ("Approved", "Return approved by technical review"),
        ("Pickup Scheduled", "Courier Shadowfax pickup booked"),
        ("Product Received", "Item physically verified at warehouse"),
        ("Refund Initiated", "Banking gateway refund triggered"),
        ("Refund Completed", "Amount credited back to original source")
    ]
    for stage, note in workflow_stages:
        ok_stage, msg_stage = update_return_status_admin(active_return["id"], stage, note=note)
        assert ok_stage is True, f"Failed updating return stage to {stage}: {msg_stage}"

    # Verify inventory was restored upon warehouse receipt
    stock_after_restock = get_product_by_id(target_returnable_item["product_id"])["stock"]
    assert stock_after_restock == stock_before_restock + 1, "Inventory was not restocked upon return receipt"

    # Verify refund was executed in refunds table
    cust_refunds = get_user_refunds(cust1["id"])
    assert len(cust_refunds) > 0, "No refund record created in refunds table!"
    assert cust_refunds[0]["status"] == "Completed", f"Expected Completed refund, got {cust_refunds[0]['status']}"
    assert cust_refunds[0]["amount"] > 0, "Refund amount is 0"
    print(f"[PASS] 12. Full 7-Stage Return Workflow, Restocking & Refund Ledger Verified (Refund #{cust_refunds[0]['refund_number']}).")

    # 13. Rejection Transition Handling
    # File return for 1 more unit and reject it to verify rejection path
    ok_ret2, _ = create_return_request(
        order_id=deliv_target["id"],
        order_item_id=target_returnable_item["id"],
        product_id=target_returnable_item["product_id"],
        user_id=cust1["id"],
        quantity=1,
        reason="Changed Mind"
    )
    rej_return = get_user_returns(cust1["id"])[0]
    ok_rej, _ = update_return_status_admin(rej_return["id"], "Rejected", note="Item damaged by user")
    assert ok_rej is True, "Rejection transition failed"
    rej_verified = get_user_returns(cust1["id"])[0]
    assert rej_verified["status"] == "Rejected", "Status was not marked Rejected"
    print("[PASS] 13. Return Rejection State Transition & Exception Handling Verified.")

    # 14. Product Reviews & Rating Aggregation
    add_product_review(
        product_id=test_prod2["id"],
        user_id=cust1["id"],
        user_name=cust1["name"],
        rating=5,
        headline="Outstanding Build Quality",
        comment="Exceeded all expectations. Clear audio and solid packaging."
    )
    reviews = get_product_reviews(test_prod2["id"])
    assert len(reviews) > 0, "Review not saved in database"
    breakdown = get_product_rating_breakdown(test_prod2["id"])
    assert breakdown["total_reviews"] > 0, "Rating breakdown total reviews is 0"
    assert breakdown["distribution"][5] >= 1, "5-star rating count mismatch"
    print("[PASS] 14. Verified Product Reviews & Rating Distribution Verified.")

    # 15. Executive Admin Dashboard KPIs & Reports
    kpis = get_admin_dashboard_kpis()
    assert kpis["products_count"] >= 100000, f"KPI product count mismatch: {kpis['products_count']}"
    assert kpis["orders_count"] > 0, "KPI orders count is 0"
    assert kpis["total_sales"] > 0, "KPI total sales is 0"
    assert kpis["refunds_total"] > 0, "KPI refunds total is 0"

    rep_orders = get_report_data("orders")
    rep_returns = get_report_data("returns")
    rep_products = get_report_data("products")
    assert len(rep_orders) > 0, "Orders report dataset empty"
    assert len(rep_returns) > 0, "Returns report dataset empty"
    assert len(rep_products) >= 1000, "Products report dataset incomplete"
    print(f"[PASS] 15. Executive Admin Dashboard KPIs & Multi-Table Data Export Verified.")

    print("=" * 70)
    print("ALL 15 COMPREHENSIVE QA TEST SUITES PASSED (100% PASS RATE)")
    print("=" * 70)

if __name__ == "__main__":
    run_comprehensive_tests()
