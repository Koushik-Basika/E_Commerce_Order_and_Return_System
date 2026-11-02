"""
E-Commerce Order and Return System — Database Module Bridge
This file provides backward compatibility for imports from database.py
by re-exporting all functions, models, and connection tools from the database package.
"""

from database.connection import get_connection, BASE_DIR, DB_PATH
from database.schema import create_schema
from database.seed_data import seed_database
from database.repository import (
    authenticate_user,
    create_user,
    update_user_profile,
    get_user_addresses,
    add_user_address,
    get_user_stats,
    get_categories,
    get_subcategories,
    get_brands,
    get_price_bounds,
    get_products_paginated,
    get_product_by_id,
    get_curated_products,
    get_related_products,
    get_user_wishlist_ids,
    get_user_wishlist_products,
    toggle_wishlist,
    get_active_coupons,
    validate_coupon,
    create_order,
    get_user_orders,
    search_orders_for_user,
    get_order_by_id,
    cancel_order,
    get_returnable_items_for_user,
    create_return_request,
    get_user_returns,
    get_user_refunds,
    get_product_reviews,
    get_product_rating_breakdown,
    is_verified_purchaser,
    add_product_review,
    get_user_notifications,
    get_unread_notification_count,
    mark_all_notifications_read,
    get_admin_dashboard_kpis,
    get_admin_sales_chart_data,
    get_admin_category_chart_data,
    get_admin_return_reasons_data,
    get_all_orders_admin,
    update_order_status_admin,
    get_all_returns_admin,
    update_return_status_admin,
    get_all_products_admin,
    add_product_admin,
    update_product_admin,
    delete_product_admin,
    quick_update_stock_admin,
    get_low_stock_products_admin,
    get_all_customers_admin,
    toggle_user_active_admin,
    get_report_data
)
from utils.auth import hash_password, verify_password

def init_db():
    create_schema()

def seed_products():
    seed_database()

def ensure_admin():
    seed_database()

def conn():
    return get_connection()
