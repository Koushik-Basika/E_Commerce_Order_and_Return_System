from importlib.metadata import distribution
import json
import sqlite3
import random
from datetime import datetime, timedelta
from .connection import get_connection
from utils.auth import hash_password, verify_password
from utils.pricing import calculate_order_pricing, calculate_item_refund_amount

# ==========================================
# 1. USER & AUTHENTICATION & ACCESS CONTROL
# ==========================================

def authenticate_user(email, password):
    """Authenticates user by email and password. Returns user dict or None."""
    if not email or not password:
        return None
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email.strip().lower(),)).fetchone()
    if row and verify_password(password, row["password"]):
        u = dict(row)
        u.pop("password", None)
        return u
    return None

def create_user(name, email, password, phone="", address=""):
    """Registers a new customer account."""
    if not name or not name.strip() or not email or not email.strip() or not password:
        return False, "Name, email, and password are required."
    try:
        with get_connection() as conn:
            now = datetime.now().isoformat(timespec="seconds")
            cur = conn.execute("""
                INSERT INTO users (name, email, password, phone, address, role, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 'customer', 1, ?)
            """, (name.strip(), email.strip().lower(), hash_password(password), phone.strip(), address.strip(), now))
            user_id = cur.lastrowid

            if address.strip():
                conn.execute("""
                    INSERT INTO addresses (user_id, full_name, phone, street_address, city, state, postal_code, is_default, created_at)
                    VALUES (?, ?, ?, ?, 'Bangalore', 'Karnataka', '560103', 1, ?)
                """, (user_id, name.strip(), phone.strip(), address.strip(), now))

            # Send welcome notification
            conn.execute("""
                INSERT INTO notifications (user_id, title, message, type, is_read, link_page, created_at)
                VALUES (?, 'Welcome to E-Commerce Order and Return System!', 'Your account has been created. Explore our catalogue and enjoy verified returns.', 'system', 0, 'shop', ?)
            """, (user_id, now))

        return True, "Registration successful! You can now log in."
    except sqlite3.IntegrityError:
        return False, "An account with that email address already exists."

def update_user_profile(user_id, name, phone, address):
    """Updates user profile details."""
    with get_connection() as conn:
        conn.execute("""
            UPDATE users SET name = ?, phone = ?, address = ? WHERE id = ?
        """, (name.strip(), phone.strip(), address.strip(), user_id))

def get_user_addresses(user_id):
    """Fetches saved addresses for a user."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC", (user_id,)).fetchall()
        return [dict(r) for r in rows]

def add_user_address(user_id, full_name, phone, street_address, city, state, postal_code, is_default=0):
    """Adds a new shipping address."""
    with get_connection() as conn:
        now = datetime.now().isoformat(timespec="seconds")
        if is_default:
            conn.execute("UPDATE addresses SET is_default = 0 WHERE user_id = ?", (user_id,))
        conn.execute("""
            INSERT INTO addresses (user_id, full_name, phone, street_address, city, state, postal_code, is_default, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, full_name.strip(), phone.strip(), street_address.strip(), city.strip(), state.strip(), postal_code.strip(), is_default, now))

def get_user_stats(user_id):
    """Fetches customer statistics summary."""
    with get_connection() as conn:
        orders_cnt = conn.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,)).fetchone()[0]
        total_spent = conn.execute("SELECT COALESCE(SUM(total), 0) FROM orders WHERE user_id = ? AND status != 'Cancelled'", (user_id,)).fetchone()[0]
        wishlist_cnt = conn.execute("SELECT COUNT(*) FROM wishlist WHERE user_id = ?", (user_id,)).fetchone()[0]
        returns_cnt = conn.execute("SELECT COUNT(*) FROM returns WHERE user_id = ?", (user_id,)).fetchone()[0]
        reviews_cnt = conn.execute("SELECT COUNT(*) FROM reviews WHERE user_id = ?", (user_id,)).fetchone()[0]
    return {
        "orders_count": orders_cnt,
        "total_spent": float(total_spent),
        "wishlist_count": wishlist_cnt,
        "returns_count": returns_cnt,
        "reviews_count": reviews_cnt
    }

# ==========================================
# 2. CATEGORIES & CATALOGUE & PAGINATION
# ==========================================

def get_categories():
    """Returns list of categories with active product counts."""
    with get_connection() as conn:
        query = """
            SELECT c.*, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON p.category = c.name AND p.status = 'active'
            GROUP BY c.id
            ORDER BY c.display_order ASC
        """
        rows = conn.execute(query).fetchall()
        return [dict(r) for r in rows]

def get_subcategories(category=None):
    """Fetches distinct subcategories for a given category."""
    with get_connection() as conn:
        if category and category != "All":
            rows = conn.execute("SELECT DISTINCT subcategory FROM products WHERE category = ? AND status = 'active' ORDER BY subcategory", (category,)).fetchall()
        else:
            rows = conn.execute("SELECT DISTINCT subcategory FROM products WHERE status = 'active' ORDER BY subcategory").fetchall()
        return [r["subcategory"] for r in rows if r["subcategory"]]

def get_brands(category=None):
    """Fetches distinct brands for a category."""
    with get_connection() as conn:
        if category and category != "All":
            rows = conn.execute("SELECT DISTINCT brand FROM products WHERE category = ? AND status = 'active' ORDER BY brand", (category,)).fetchall()
        else:
            rows = conn.execute("SELECT DISTINCT brand FROM products WHERE status = 'active' ORDER BY brand").fetchall()
        return [r["brand"] for r in rows if r["brand"]]

def get_price_bounds(category=None):
    """Returns min and max price for category."""
    with get_connection() as conn:
        if category and category != "All":
            row = conn.execute("SELECT MIN(price) min_p, MAX(price) max_p FROM products WHERE category = ? AND status = 'active'", (category,)).fetchone()
        else:
            row = conn.execute("SELECT MIN(price) min_p, MAX(price) max_p FROM products WHERE status = 'active'").fetchone()
    min_p = float(row["min_p"] or 0)
    max_p = float(row["max_p"] or 150000)
    return min_p, max_p

def get_products_paginated(
    search="",
    category="All",
    subcategory="All",
    brand="All",
    min_price=None,
    max_price=None,
    min_rating=0,
    min_discount=0,
    in_stock_only=False,
    sort_by="Relevance",
    page=1,
    per_page=24
):
    """High-performance server-side paginated, filtered, and searched product query."""
    with get_connection() as conn:
        conditions = ["status = 'active'"]
        params = []

        if search and search.strip():
            terms = f"%{search.strip().lower()}%"
            conditions.append("(LOWER(name) LIKE ? OR LOWER(brand) LIKE ? OR LOWER(category) LIKE ? OR LOWER(subcategory) LIKE ? OR LOWER(description) LIKE ? OR LOWER(sku) LIKE ?)")
            params.extend([terms, terms, terms, terms, terms, terms])

        if category and category != "All":
            conditions.append("category = ?")
            params.append(category)

        if subcategory and subcategory != "All":
            conditions.append("subcategory = ?")
            params.append(subcategory)

        if brand and brand != "All":
            conditions.append("brand = ?")
            params.append(brand)

        if min_price is not None:
            conditions.append("price >= ?")
            params.append(float(min_price))

        if max_price is not None:
            conditions.append("price <= ?")
            params.append(float(max_price))

        if min_rating > 0:
            conditions.append("rating >= ?")
            params.append(float(min_rating))

        if min_discount > 0:
            conditions.append("discount_percent >= ?")
            params.append(int(min_discount))

        if in_stock_only:
            conditions.append("stock > 0")

        where_clause = " WHERE " + " AND ".join(conditions)

        # Count total matches efficiently
        count_sql = f"SELECT COUNT(*) FROM products {where_clause}"
        total_count = conn.execute(count_sql, params).fetchone()[0]

        # Sorting
        sort_map = {
            "Relevance": "id DESC",
            "Popularity": "review_count DESC",
            "Price: Low to High": "price ASC",
            "Price: High to Low": "price DESC",
            "Rating": "rating DESC",
            "Newest": "id DESC",
            "Biggest Discount": "discount_percent DESC",
            "Most Reviewed": "review_count DESC"
        }
        order_by = sort_map.get(sort_by, "id DESC")

        # Server-side Pagination
        offset = max(0, (page - 1) * per_page)
        data_sql = f"SELECT * FROM products {where_clause} ORDER BY {order_by} LIMIT ? OFFSET ?"
        data_params = params + [per_page, offset]

        rows = conn.execute(data_sql, data_params).fetchall()
        items = [dict(r) for r in rows]

        total_pages = max(1, (total_count + per_page - 1) // per_page)

        return {
            "items": items,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page
        }

def get_product_by_id(product_id):
    """Fetches a single product by ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return dict(row) if row else None

def get_curated_products(criteria="trending", limit=8):
    """Fetches curated products based on criteria."""
    with get_connection() as conn:
        if criteria == "trending":
            sql = "SELECT * FROM products WHERE status = 'active' ORDER BY rating DESC, review_count DESC LIMIT ?"
        elif criteria == "deals":
            sql = "SELECT * FROM products WHERE status = 'active' AND discount_percent >= 20 ORDER BY discount_percent DESC LIMIT ?"
        elif criteria == "bestsellers":
            sql = "SELECT * FROM products WHERE status = 'active' ORDER BY review_count DESC LIMIT ?"
        elif criteria == "top_rated":
            sql = "SELECT * FROM products WHERE status = 'active' AND rating >= 4.4 ORDER BY rating DESC, review_count DESC LIMIT ?"
        else:
            sql = "SELECT * FROM products WHERE status = 'active' ORDER BY id DESC LIMIT ?"
        rows = conn.execute(sql, (limit,)).fetchall()
        return [dict(r) for r in rows]

def get_related_products(product_id, category, brand, limit=4):
    """Fetches related products within the same category or brand."""
    with get_connection() as conn:
        sql = """
            SELECT * FROM products
            WHERE id != ? AND status = 'active' AND (category = ? OR brand = ?)
            ORDER BY rating DESC LIMIT ?
        """
        rows = conn.execute(sql, (product_id, category, brand, limit)).fetchall()
        return [dict(r) for r in rows]

# ==========================================
# 3. WISHLIST
# ==========================================

def get_user_wishlist_ids(user_id):
    """Returns set of product IDs in user's wishlist."""
    with get_connection() as conn:
        rows = conn.execute("SELECT product_id FROM wishlist WHERE user_id = ?", (user_id,)).fetchall()
        return {r["product_id"] for r in rows}

def get_user_wishlist_products(user_id):
    """Returns detailed products saved in wishlist."""
    with get_connection() as conn:
        query = """
            SELECT p.*, w.created_at as wishlisted_at
            FROM wishlist w
            JOIN products p ON p.id = w.product_id
            WHERE w.user_id = ? AND p.status = 'active'
            ORDER BY w.id DESC
        """
        rows = conn.execute(query, (user_id,)).fetchall()
        return [dict(r) for r in rows]

def toggle_wishlist(user_id, product_id):
    """Adds product to wishlist if absent, removes if present. Returns new boolean state."""
    with get_connection() as conn:
        exists = conn.execute("SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?", (user_id, product_id)).fetchone()
        now = datetime.now().isoformat(timespec="seconds")
        if exists:
            conn.execute("DELETE FROM wishlist WHERE user_id = ? AND product_id = ?", (user_id, product_id))
            return False
        else:
            conn.execute("INSERT INTO wishlist (user_id, product_id, created_at) VALUES (?, ?, ?)", (user_id, product_id, now))
            return True

# ==========================================
# 4. COUPONS & PRICING
# ==========================================

def get_active_coupons():
    """Fetches all active coupons."""
    with get_connection() as conn:
        now_str = datetime.now().strftime("%Y-%m-%d")
        rows = conn.execute("SELECT * FROM coupons WHERE is_active = 1 AND (expiry_date IS NULL OR expiry_date >= ?) ORDER BY discount_value DESC", (now_str,)).fetchall()
        return [dict(r) for r in rows]

def validate_coupon(code, cart_subtotal):
    """Validates coupon and calculates discount amount."""
    code_clean = str(code).strip().upper()
    with get_connection() as conn:
        now_str = datetime.now().strftime("%Y-%m-%d")
        coupon = conn.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code_clean,)).fetchone()
        if not coupon:
            return {"valid": False, "discount": 0.0, "message": "Invalid coupon code."}

        c = dict(coupon)
        if c["expiry_date"] and c["expiry_date"] < now_str:
            return {"valid": False, "discount": 0.0, "message": "Coupon has expired."}

        if cart_subtotal < c["min_order_amount"]:
            return {"valid": False, "discount": 0.0, "message": f"Minimum order amount for {code_clean} is ₹{c['min_order_amount']:,.0f}."}

        if c["usage_limit"] and c["times_used"] >= c["usage_limit"]:
            return {"valid": False, "discount": 0.0, "message": "Coupon usage limit has been reached."}

        discount = 0.0
        if c["discount_type"] == "percent":
            discount = (cart_subtotal * c["discount_value"]) / 100.0
            if c["max_discount"] > 0:
                discount = min(discount, c["max_discount"])
        else:
            discount = c["discount_value"]

        discount = min(discount, cart_subtotal)
        return {
            "valid": True,
            "discount": round(discount, 2),
            "code": code_clean,
            "message": f"Coupon applied! You saved ₹{discount:,.2f}."
        }

# ==========================================
# 5. ORDER CREATION & MANAGEMENT
# ==========================================

def create_order(user_id, cart_dict, shipping_address, delivery_method="Standard", payment_method="UPI", coupon_code="", discount=0.0):
    """
    Creates a new order under atomic transaction.
    Recalculates pricing, stock, tax, shipping, and discounts on the server.
    """
    if not cart_dict:
        return False, "Cart is empty.", None
    if not shipping_address or not shipping_address.strip():
        return False, "Delivery address is required.", None

    with get_connection() as conn:
        # Use centralized server-side pricing service to verify cart, inventory and pricing
        pricing = calculate_order_pricing(conn, cart_dict, coupon_code, delivery_method)
        if not pricing["valid"]:
            return False, pricing["error"], None

        subtotal = pricing["subtotal"]
        discount = pricing["discount"]
        coupon_applied = pricing["coupon_code"]
        delivery_fee = pricing["delivery_fee"]
        tax_amount = pricing["tax_amount"]
        total = pricing["total"]
        verified_items = pricing["items"]

        now = datetime.now()
        order_num = f"ORD-{now.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        exp_days = 2 if delivery_method == "Express" else 4
        expected_delivery = (now + timedelta(days=exp_days)).strftime("%Y-%m-%d")

        tracking_history = json.dumps([
            {"status": "Placed", "time": now.strftime("%Y-%m-%d %H:%M"), "note": "Order placed successfully"}
        ])

        # Insert Order Record
        cur = conn.execute("""
            INSERT INTO orders (
                order_number, user_id, subtotal, discount, coupon_code, delivery_fee,
                tax_amount, total, shipping_address, delivery_method, payment_method,
                payment_status, status, expected_delivery, delivery_date, tracking_history, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Placed', ?, NULL, ?, ?, ?)
        """, (
            order_num, user_id, subtotal, discount, coupon_applied, delivery_fee,
            tax_amount, total, shipping_address.strip(), delivery_method, payment_method,
            "COD" if payment_method == "Cash on Delivery" else "Paid", expected_delivery,
            tracking_history, now.isoformat(timespec="seconds"), now.isoformat(timespec="seconds")
        ))
        order_id = cur.lastrowid

        # Insert Order Items and Atomically Decrement Inventory
        for it in verified_items:
            conn.execute("""
                INSERT INTO order_items (
                    order_id, product_id, product_name, brand, image_url,
                    quantity, returned_quantity, price, total_price, has_return
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, 0)
            """, (
                order_id, it["product_id"], it["name"], it["brand"], it["image_url"],
                it["quantity"], it["unit_price"], it["total_price"]
            ))

            # Stock reduction with optimistic locking check
            stock_cur = conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                (it["quantity"], it["product_id"], it["quantity"])
            )
            if stock_cur.rowcount == 0:
                conn.rollback()
                return False, f"Stock changed concurrently for '{it['name']}'. Please retry.", None

        # Record coupon usage if applicable
        if coupon_applied:
            conn.execute("UPDATE coupons SET times_used = times_used + 1 WHERE code = ?", (coupon_applied,))

        # Notification & Audit
        conn.execute("""
            INSERT INTO notifications (user_id, title, message, type, is_read, link_page, created_at)
            VALUES (?, 'Order Confirmed!', ?, 'order', 0, 'orders', ?)
        """, (user_id, f"Your order #{order_num} has been placed successfully. Expected delivery by {expected_delivery}.", now.isoformat(timespec="seconds")))

        conn.execute("""
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, created_at)
            VALUES (?, 'ORDER_CREATED', 'order', ?, ?, ?)
        """, (user_id, order_id, f"Order #{order_num} created for total ₹{total}", now.isoformat(timespec="seconds")))

        return True, f"Order #{order_num} placed successfully!", order_num

def get_user_orders(user_id, status_filter="All", search=""):
    """Fetches user orders with line items (strict customer data isolation and search filtering)."""
    with get_connection() as conn:
        where = ["user_id = ?"]
        params = [user_id]

        if status_filter and status_filter != "All":
            where.append("status = ?")
            params.append(status_filter)

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            where.append("(LOWER(order_number) LIKE ? OR LOWER(shipping_address) LIKE ? OR LOWER(payment_method) LIKE ?)")
            params.extend([term, term, term])

        query = f"SELECT * FROM orders WHERE {' AND '.join(where)} ORDER BY id DESC"
        rows = conn.execute(query, params).fetchall()

        orders = [dict(r) for r in rows]
        for o in orders:
            items = conn.execute("""
                SELECT oi.*, p.category, p.subcategory
                FROM order_items oi
                LEFT JOIN products p ON p.id = oi.product_id
                WHERE oi.order_id = ?
            """, (o["id"],)).fetchall()
            o["items"] = [dict(it) for it in items]
            try:
                o["tracking_list"] = json.loads(o["tracking_history"]) if o["tracking_history"] else []
            except Exception:
                o["tracking_list"] = []
        return orders

def search_orders_for_user(user_id, query, is_admin=False):
    """
    Searches orders strictly respecting authorization boundary.
    Normal customers only search their own orders; admins can search all orders.
    """
    if not query or not query.strip():
        return []
    clean_q = query.strip()
    if is_admin:
        return get_all_orders_admin(search=clean_q)
    return get_user_orders(user_id, search=clean_q)

def get_order_by_id(order_id, user_id=None):
    """Fetches full order details by ID with optional user authorization check."""
    with get_connection() as conn:
        if user_id:
            row = conn.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id)).fetchone()
        else:
            row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return None
        o = dict(row)
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
        o["items"] = [dict(it) for it in items]
        try:
            o["tracking_list"] = json.loads(o["tracking_history"]) if o["tracking_history"] else []
        except Exception:
            o["tracking_list"] = []
        return o

def cancel_order(order_id, user_id, reason="Customer cancelled"):
    """Cancels order if in Placed or Confirmed state, restores product stock, logs audit trail."""
    with get_connection() as conn:
        order = conn.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id)).fetchone()
        if not order:
            return False, "Order not found or access denied."
        if order["status"] not in ("Placed", "Confirmed"):
            return False, f"Order cannot be cancelled in '{order['status']}' state. Eligible for return once delivered."

        now = datetime.now()
        # Restore stock to warehouse inventory
        items = conn.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
        for it in items:
            conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (it["quantity"], it["product_id"]))

        # Update tracking history
        try:
            hist = json.loads(order["tracking_history"]) if order["tracking_history"] else []
        except Exception:
            hist = []
        hist.append({"status": "Cancelled", "time": now.strftime("%Y-%m-%d %H:%M"), "note": f"Cancelled by user: {reason}"})

        conn.execute("""
            UPDATE orders SET status = 'Cancelled', tracking_history = ?, updated_at = ? WHERE id = ?
        """, (json.dumps(hist), now.isoformat(timespec="seconds"), order_id))

        # Notification & Audit
        conn.execute("""
            INSERT INTO notifications (user_id, title, message, type, is_read, link_page, created_at)
            VALUES (?, 'Order Cancelled', ?, 'order', 0, 'orders', ?)
        """, (user_id, f"Order #{order['order_number']} has been cancelled.", now.isoformat(timespec="seconds")))

        conn.execute("""
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, created_at)
            VALUES (?, 'CANCEL_ORDER', 'order', ?, ?, ?)
        """, (user_id, order_id, f"Order cancelled: {reason}", now.isoformat(timespec="seconds")))

        return True, f"Order #{order['order_number']} cancelled successfully."

# ==========================================
# 6. RETURNS & REFUNDS (CORE FEATURE)
# ==========================================

VALID_RETURN_TRANSITIONS = {
    "Return Requested": ["Under Review", "Approved", "Rejected"],
    "Under Review": ["Under Review", "Approved", "Rejected"],
    "Approved": ["Pickup Scheduled", "Product Received", "Rejected"],
    "Pickup Scheduled": ["Product Received", "Rejected"],
    "Product Received": ["Refund Initiated", "Rejected"],
    "Refund Initiated": ["Refund Completed"],
    "Refund Completed": [],
    "Rejected": []
}

def get_returnable_items_for_user(user_id):
    """
    Returns items from Delivered orders that have remaining returnable quantity within policy window.
    Supports partial returns and enforces delivery date validation.
    """
    with get_connection() as conn:
        query = """
            SELECT oi.*, 
                   (oi.quantity - COALESCE(oi.returned_quantity, 0)) as returnable_quantity,
                   o.order_number, o.created_at as order_date, o.delivery_date, o.status as order_status, 
                   p.category, p.return_policy
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN products p ON p.id = oi.product_id
            WHERE o.user_id = ? 
              AND o.status = 'Delivered' 
              AND (oi.quantity - COALESCE(oi.returned_quantity, 0)) > 0
            ORDER BY o.id DESC
        """
        rows = conn.execute(query, (user_id,)).fetchall()
        now = datetime.now()
        valid_items = []
        for r in rows:
            d = dict(r)
            # Check delivery return window (graceful 30 days window covers all 7-14 day return policies)
            date_str = d.get("delivery_date") or d.get("order_date") or ""
            try:
                clean_date = date_str.replace("T", " ").split(".")[0]
                dt = datetime.fromisoformat(clean_date)
                if (now - dt).days <= 30:
                    valid_items.append(d)
            except Exception:
                valid_items.append(d)
        return valid_items

def create_return_request(order_id, order_item_id, product_id, user_id, quantity, reason, comments="", refund_method="Original Payment"):
    """
    Submits a return request with full workflow tracking and customer notification.
    Validates delivery status, return window, partial quantities, and calculates fair refund.
    """
    with get_connection() as conn:
        order = conn.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id)).fetchone()
        if not order:
            return False, "Order not found or access denied."
        if order["status"] != "Delivered":
            return False, f"Only delivered orders are eligible for return (current status: '{order['status']}')."

        # Check return window
        now = datetime.now()
        date_str = order["delivery_date"] or order["updated_at"] or order["created_at"]
        try:
            clean_date = date_str.replace("T", " ").split(".")[0]
            dt = datetime.fromisoformat(clean_date)
            if (now - dt).days > 30:
                return False, "Return window has expired. Returns must be requested within return policy timeframe."
        except Exception:
            pass

        item = conn.execute("SELECT * FROM order_items WHERE id = ? AND order_id = ?", (order_item_id, order_id)).fetchone()
        if not item:
            return False, "Order item not found in specified order."

        returned_qty = item["returned_quantity"] or 0
        available_to_return = item["quantity"] - returned_qty
        if available_to_return <= 0:
            return False, "All purchased units of this item have already been returned."

        quantity = int(quantity)
        if quantity <= 0:
            return False, "Return quantity must be at least 1."
        if quantity > available_to_return:
            return False, f"Invalid return quantity {quantity}. Only {available_to_return} returnable units remain."

        ret_num = f"RET-{now.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

        tracking = json.dumps([
            {"status": "Under Review", "time": now.strftime("%Y-%m-%d %H:%M"), "note": f"Reason: {reason}. Comments: {comments or 'None'}"}
        ])

        # Stage 1: Under Review
        cur = conn.execute("""
            INSERT INTO returns (
                return_number, order_id, order_item_id, product_id, user_id, quantity,
                reason, comments, refund_method, status, tracking_history, restocked, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Under Review', ?, 0, ?, ?)
        """, (
            ret_num, order_id, order_item_id, product_id, user_id, quantity,
            reason, comments.strip(), refund_method, tracking,
            now.isoformat(timespec="seconds"), now.isoformat(timespec="seconds")
        ))
        ret_id = cur.lastrowid

        # Update order item returned quantity and flag
        new_returned_qty = returned_qty + quantity
        has_ret_flag = 1 if new_returned_qty >= item["quantity"] else 0
        conn.execute("UPDATE order_items SET returned_quantity = ?, has_return = ? WHERE id = ?", (new_returned_qty, has_ret_flag, order_item_id))

        # Notification & Audit
        conn.execute("""
            INSERT INTO notifications (user_id, title, message, type, is_read, link_page, created_at)
            VALUES (?, 'Return Request Received 📦', ?, 'return', 0, 'returns', ?)
        """, (user_id, f"Your return request #{ret_num} for order #{order['order_number']} is under review.", now.isoformat(timespec="seconds")))

        conn.execute("""
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, created_at)
            VALUES (?, 'CREATE_RETURN', 'return', ?, ?, ?)
        """, (user_id, ret_id, f"Return filed for {quantity}x item #{product_id} from order #{order['order_number']}", now.isoformat(timespec="seconds")))

        return True, f"Return request #{ret_num} submitted successfully! Your request is currently Under Review."

def get_user_returns(user_id):
    """Fetches all return requests filed by a user with product and order details."""
    with get_connection() as conn:
        query = """
            SELECT r.*, o.order_number, p.name as product_name, p.brand, p.image_url, p.price as unit_price,
                   ref.status as refund_status, ref.amount as refund_amount, ref.refund_number
            FROM returns r
            JOIN orders o ON o.id = r.order_id
            JOIN products p ON p.id = r.product_id
            LEFT JOIN refunds ref ON ref.return_id = r.id
            WHERE r.user_id = ?
            ORDER BY r.id DESC
        """
        rows = conn.execute(query, (user_id,)).fetchall()
        returns_list = [dict(r) for r in rows]
        for r in returns_list:
            try:
                r["tracking_list"] = json.loads(r["tracking_history"]) if r["tracking_history"] else []
            except Exception:
                r["tracking_list"] = []
        return returns_list

def get_user_refunds(user_id):
    """Fetches all refunds for a user."""
    with get_connection() as conn:
        query = """
            SELECT ref.*, o.order_number, p.name as product_name, p.brand, p.image_url
            FROM refunds ref
            JOIN orders o ON o.id = ref.order_id
            JOIN products p ON p.id = ref.product_id
            WHERE ref.user_id = ?
            ORDER BY ref.id DESC
        """
        rows = conn.execute(query, (user_id,)).fetchall()
        return [dict(r) for r in rows]

# ==========================================
# 7. REVIEWS & RATINGS
# ==========================================

def get_product_reviews(product_id):
    """Fetches verified reviews for a product."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM reviews WHERE product_id = ? ORDER BY id DESC", (product_id,)).fetchall()
        return [dict(r) for r in rows]

def get_product_rating_breakdown(product_id):
    """Calculates star distribution and average rating."""
    with get_connection() as conn:
        rows = conn.execute("SELECT rating FROM reviews WHERE product_id = ?", (product_id,)).fetchall()
        total = len(rows)
        if total == 0:
            return {"avg": 4.5, "total_reviews": 0, "distribution": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}}
        counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for r in rows:
            counts[r["rating"]] = counts.get(r["rating"], 0) + 1
        avg = sum(k * v for k, v in counts.items()) / total
        return {
            "avg": round(avg, 1),
            "total_reviews": total,
            "average_rating": avg,
            "distribution": distribution,
            "counts": counts
        }

def is_verified_purchaser(user_id, product_id):
    """Checks whether user has purchased the item and had it delivered."""
    if not user_id:
        return False
    with get_connection() as conn:
        row = conn.execute("""
            SELECT oi.id FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.user_id = ? AND oi.product_id = ? AND o.status = 'Delivered'
        """, (user_id, product_id)).fetchone()
        return bool(row)

def add_product_review(product_id, user_id, user_name, rating, headline, comment):
    """Adds a new verified user review and updates product aggregate rating."""
    if not headline.strip() or not comment.strip():
        return False, "Headline and review comments are required."
    with get_connection() as conn:
        now = datetime.now().isoformat(timespec="seconds")
        is_verified = int(is_verified_purchaser(user_id, product_id))
        conn.execute("""
            INSERT INTO reviews (product_id, user_id, user_name, rating, headline, comment, verified_purchase, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, user_id, user_name, int(rating), headline.strip(), comment.strip(), is_verified, now, now))

        # Recompute aggregate rating
        stats = conn.execute("SELECT AVG(rating) as avg_r, COUNT(*) as cnt FROM reviews WHERE product_id = ?", (product_id,)).fetchone()
        if stats and stats["cnt"]:
            conn.execute("UPDATE products SET rating = ?, review_count = ? WHERE id = ?", (round(stats["avg_r"], 1), stats["cnt"], product_id))

        return True, "Review submitted successfully!"

# ==========================================
# 8. NOTIFICATIONS & AUDIT
# ==========================================

def get_user_notifications(user_id):
    """Fetches user notifications."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT 20", (user_id,)).fetchall()
        return [dict(r) for r in rows]

def get_unread_notification_count(user_id):
    """Counts unread notifications."""
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,)).fetchone()[0]

def mark_all_notifications_read(user_id):
    """Marks all notifications as read."""
    with get_connection() as conn:
        conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))

# ==========================================
# 9. ADMIN OPERATIONS & DASHBOARD KPIS
# ==========================================

def get_admin_dashboard_kpis():
    """Calculates live KPI metrics for Executive Dashboard."""
    with get_connection() as conn:
        total_sales = conn.execute("SELECT COALESCE(SUM(total), 0) FROM orders WHERE status != 'Cancelled'").fetchone()[0]
        orders_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        customers_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'").fetchone()[0]
        products_count = conn.execute("SELECT COUNT(*) FROM products WHERE status = 'active'").fetchone()[0]
        returns_count = conn.execute("SELECT COUNT(*) FROM returns").fetchone()[0]
        refunds_total = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM refunds WHERE status = 'Completed'").fetchone()[0]
    return {
        "total_sales": float(total_sales),
        "orders_count": orders_count,
        "customers_count": customers_count,
        "products_count": products_count,
        "returns_count": returns_count,
        "refunds_total": float(refunds_total)
    }

def get_admin_sales_chart_data():
    """Returns daily gross sales for analytics charts."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT SUBSTR(created_at, 1, 10) as day, COUNT(*) as orders_count, SUM(total) as revenue
            FROM orders
            WHERE status != 'Cancelled'
            GROUP BY SUBSTR(created_at, 1, 10)
            ORDER BY day ASC
        """).fetchall()
        return [dict(r) for r in rows]

def get_admin_category_chart_data():
    """Returns category-wise product count for distribution charts."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT category, COUNT(*) as product_count
            FROM products
            WHERE status = 'active'
            GROUP BY category
            ORDER BY product_count DESC
        """).fetchall()
        return [dict(r) for r in rows]

def get_admin_return_reasons_data():
    """Returns breakdown of return reasons."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT reason, COUNT(*) as count
            FROM returns
            GROUP BY reason
            ORDER BY count DESC
        """).fetchall()
        return [dict(r) for r in rows]

def get_all_orders_admin(search="", status="All"):
    """Fetches all orders across all customers for admin management."""
    with get_connection() as conn:
        where = ["1=1"]
        params = []
        if search.strip():
            terms = f"%{search.strip().lower()}%"
            where.append("(LOWER(o.order_number) LIKE ? OR LOWER(u.name) LIKE ? OR LOWER(u.email) LIKE ?)")
            params.extend([terms, terms, terms])
        if status != "All":
            where.append("o.status = ?")
            params.append(status)

        query = f"""
            SELECT o.*, u.name as customer_name, u.email as customer_email, u.phone as customer_phone
            FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE {" AND ".join(where)}
            ORDER BY o.id DESC
        """
        rows = conn.execute(query, params).fetchall()
        order_list = [dict(r) for r in rows]
        for o in order_list:
            items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],)).fetchall()
            o["items"] = [dict(it) for it in items]
        return order_list

VALID_ORDER_TRANSITIONS = {
    "Placed": ["Confirmed", "Cancelled"],
    "Confirmed": ["Packed", "Cancelled"],
    "Packed": ["Shipped"],
    "Shipped": ["Out for Delivery"],
    "Out for Delivery": ["Delivered"],
    "Delivered": [],
    "Cancelled": []
}

def update_order_status_admin(order_id, new_status, note="", admin_user_id=1):
    """Updates order status along with visual timeline and delivery tracking."""
    with get_connection() as conn:
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            return False, "Order not found."

        current_status = order["status"]
        allowed = VALID_ORDER_TRANSITIONS.get(current_status, [])
        if new_status not in allowed and new_status != current_status:
            return False, f"Invalid order transition: '{current_status}' -> '{new_status}'. Allowed: {', '.join(allowed) or 'Terminal state'}."

        now = datetime.now()
        try:
            hist = json.loads(order["tracking_history"]) if order["tracking_history"] else []
        except Exception:
            hist = []

        hist.append({
            "status": new_status,
            "time": now.strftime("%Y-%m-%d %H:%M"),
            "note": note or f"Status updated to {new_status}"
        })

        if new_status == "Delivered":
            del_date = now.isoformat(timespec="seconds")
            conn.execute("""
                UPDATE orders SET status = ?, delivery_date = ?, tracking_history = ?, updated_at = ? WHERE id = ?
            """, (new_status, del_date, json.dumps(hist), del_date, order_id))
        elif new_status == "Cancelled":
            # Restore stock if cancelled by admin
            items = conn.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
            for it in items:
                conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (it["quantity"], it["product_id"]))
            conn.execute("""
                UPDATE orders SET status = 'Cancelled', tracking_history = ?, updated_at = ? WHERE id = ?
            """, (json.dumps(hist), now.isoformat(timespec="seconds"), order_id))
        else:
            conn.execute("""
                UPDATE orders SET status = ?, tracking_history = ?, updated_at = ? WHERE id = ?
            """, (new_status, json.dumps(hist), now.isoformat(timespec="seconds"), order_id))

        # Notification & audit
        conn.execute("""
            INSERT INTO notifications (user_id, title, message, type, is_read, link_page, created_at)
            VALUES (?, ?, ?, 'order', 0, 'orders', ?)
        """, (order["user_id"], f"Order #{order['order_number']} is {new_status}", f"Update: {note or new_status}", now.isoformat(timespec="seconds")))

        conn.execute("""
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, created_at)
            VALUES (?, 'UPDATE_ORDER_STATUS', 'order', ?, ?, ?)
        """, (admin_user_id, order_id, f"Order status changed to {new_status}", now.isoformat(timespec="seconds")))

        return True, f"Order status updated to '{new_status}'."

def get_all_returns_admin(search="", status="All"):
    """Admin return request overview across all users."""
    with get_connection() as conn:
        where = ["1=1"]
        params = []
        if search.strip():
            terms = f"%{search.strip().lower()}%"
            where.append("(LOWER(r.return_number) LIKE ? OR LOWER(o.order_number) LIKE ? OR LOWER(u.name) LIKE ? OR LOWER(p.name) LIKE ?)")
            params.extend([terms, terms, terms, terms])
        if status != "All":
            where.append("r.status = ?")
            params.append(status)

        query = f"""
            SELECT r.*, o.order_number, u.name as customer_name, u.email as customer_email, u.phone as customer_phone,
                   p.name as product_name, p.brand, p.image_url, p.price as unit_price,
                   ref.status as refund_status, ref.amount as refund_amount, ref.refund_number
            FROM returns r
            JOIN orders o ON o.id = r.order_id
            JOIN users u ON u.id = r.user_id
            JOIN products p ON p.id = r.product_id
            LEFT JOIN refunds ref ON ref.return_id = r.id
            WHERE {" AND ".join(where)}
            ORDER BY r.id DESC
        """
        rows = conn.execute(query, params).fetchall()
        ret_list = [dict(r) for r in rows]
        for r in ret_list:
            try:
                r["tracking_list"] = json.loads(r["tracking_history"]) if r["tracking_history"] else []
            except Exception:
                r["tracking_list"] = []
        return ret_list

def update_return_status_admin(return_id, new_status, note="", pickup_date=None, admin_user_id=1):
    """
    Advances return status through the verified 7-stage pipeline and handles refunds and restocking.
    Enforces valid state transition matrix.
    """
    with get_connection() as conn:
        ret = conn.execute("SELECT * FROM returns WHERE id = ?", (return_id,)).fetchone()
        if not ret:
            return False, "Return not found."

        current_status = ret["status"]
        allowed_next = VALID_RETURN_TRANSITIONS.get(current_status, [])
        if new_status not in allowed_next and new_status != current_status:
            return False, f"Invalid state transition: Cannot transition from '{current_status}' to '{new_status}'. Allowed next stages: {', '.join(allowed_next) or 'None (Terminal state)'}."

        now = datetime.now()
        try:
            hist = json.loads(ret["tracking_history"]) if ret["tracking_history"] else []
        except Exception:
            hist = []

        hist.append({
            "status": new_status,
            "time": now.strftime("%Y-%m-%d %H:%M"),
            "note": note or f"Return stage updated to {new_status}"
        })

        update_sql = "UPDATE returns SET status = ?, tracking_history = ?, updated_at = ?"
        update_params = [new_status, json.dumps(hist), now.isoformat(timespec="seconds")]

        if pickup_date:
            update_sql += ", pickup_date = ?"
            update_params.append(pickup_date)

        update_sql += " WHERE id = ?"
        update_params.append(return_id)
        conn.execute(update_sql, update_params)

        # If return is rejected, roll back reserved return quantity on order item
        if new_status == "Rejected":
            conn.execute("""
                UPDATE order_items 
                SET returned_quantity = MAX(0, COALESCE(returned_quantity, 0) - ?),
                    has_return = 0
                WHERE id = ?
            """, (ret["quantity"], ret["order_item_id"]))

        # Restock product upon physical receipt at warehouse
        if new_status in ("Product Received", "Refund Completed") and not ret["restocked"]:
            conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (ret["quantity"], ret["product_id"]))
            conn.execute("UPDATE returns SET restocked = 1 WHERE id = ?", (return_id,))

        # Refund handling
        if new_status in ("Refund Initiated", "Refund Completed"):
            item = conn.execute("SELECT * FROM order_items WHERE id = ?", (ret["order_item_id"],)).fetchone()
            order = conn.execute("SELECT * FROM orders WHERE id = ?", (ret["order_id"],)).fetchone()
            refund_amt = calculate_item_refund_amount(item["price"] if item else 0.0, ret["quantity"], order["subtotal"] if order else 0.0, order["discount"] if order else 0.0)

            ref_exists = conn.execute("SELECT id FROM refunds WHERE return_id = ?", (return_id,)).fetchone()
            if not ref_exists:
                ref_num = f"REF-{now.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                txn_id = f"TXN_{random.randint(100000000, 999999999)}"
                conn.execute("""
                    INSERT INTO refunds (
                        refund_number, return_id, order_id, user_id, product_id,
                        amount, method, status, transaction_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ref_num, return_id, ret["order_id"], ret["user_id"], ret["product_id"],
                    refund_amt, ret["refund_method"], "Completed" if new_status == "Refund Completed" else "Processing",
                    txn_id, now.isoformat(timespec="seconds"), now.isoformat(timespec="seconds")
                ))
            else:
                conn.execute("""
                    UPDATE refunds SET status = ?, amount = ?, updated_at = ? WHERE return_id = ?
                """, ("Completed" if new_status == "Refund Completed" else "Processing", refund_amt, now.isoformat(timespec="seconds"), return_id))

        # Audit log
        conn.execute("""
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, created_at)
            VALUES (?, 'UPDATE_RETURN_STATUS', 'return', ?, ?, ?)
        """, (admin_user_id, return_id, f"Return status updated from {current_status} to {new_status}. Note: {note}", now.isoformat(timespec="seconds")))

        # Notify customer
        conn.execute("""
            INSERT INTO notifications (user_id, title, message, type, is_read, link_page, created_at)
            VALUES (?, ?, ?, 'return', 0, 'returns', ?)
        """, (ret["user_id"], f"Return #{ret['return_number']} Status: {new_status}", f"Update on return #{ret['return_number']}: {note or new_status}", now.isoformat(timespec="seconds")))

        return True, f"Return status updated to '{new_status}'."

def get_all_products_admin(search="", category="All", stock_filter="All", page=1, per_page=20):
    """Admin product listing with inventory filters."""
    with get_connection() as conn:
        conditions = []
        params = []
        if search.strip():
            terms = f"%{search.strip().lower()}%"
            conditions.append("(LOWER(name) LIKE ? OR LOWER(sku) LIKE ? OR LOWER(brand) LIKE ?)")
            params.extend([terms, terms, terms])
        if category != "All":
            conditions.append("category = ?")
            params.append(category)
        if stock_filter == "Out of Stock":
            conditions.append("stock = 0")
        elif stock_filter == "Low Stock (<=5)":
            conditions.append("stock > 0 AND stock <= 5")
        elif stock_filter == "In Stock (>5)":
            conditions.append("stock > 5")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        total = conn.execute(f"SELECT COUNT(*) FROM products {where}", params).fetchone()[0]

        offset = (page - 1) * per_page
        rows = conn.execute(f"SELECT * FROM products {where} ORDER BY id DESC LIMIT ? OFFSET ?", params + [per_page, offset]).fetchall()
        return [dict(r) for r in rows], total

def add_product_admin(p):
    """Adds a new product into catalogue with SKU and duplicate validation."""
    with get_connection() as conn:
        now = datetime.now().isoformat(timespec="seconds")
        sku = p.get("sku") or f"SKU-{p['category'][:3].upper()}-{random.randint(2000, 9999)}"
        sku = sku.strip().upper()

        # Check duplicate SKU
        dup = conn.execute("SELECT id FROM products WHERE sku = ?", (sku,)).fetchone()
        if dup:
            return False, f"A product with SKU '{sku}' already exists in catalogue."

        # Check duplicate Name + Brand in Category
        dup_name = conn.execute(
            "SELECT id FROM products WHERE LOWER(name) = ? AND LOWER(brand) = ? AND category = ? AND status = 'active'",
            (p["name"].strip().lower(), p["brand"].strip().lower(), p["category"].strip())
        ).fetchone()
        if dup_name:
            return False, f"A product named '{p['name']}' by brand '{p['brand']}' already exists in {p['category']}."

        disc = int(round((float(p["original_price"]) - float(p["price"])) / float(p["original_price"]) * 100)) if float(p.get("original_price", 0)) > 0 else 0
        conn.execute("""
            INSERT INTO products (
                name, brand, category, subcategory, description, price, original_price,
                discount_percent, stock, sku, rating, review_count, image_url,
                specifications, warranty, delivery_days, return_policy, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
        """, (
            p["name"].strip(), p["brand"].strip(), p["category"].strip(), p["subcategory"].strip(),
            p.get("description", "").strip(), float(p["price"]), float(p["original_price"]),
            disc, int(p["stock"]), sku, float(p.get("rating", 4.5)), int(p.get("review_count", 0)),
            p.get("image_url", "").strip(), p.get("specifications", "{}"),
            p.get("warranty", "1 Year Manufacturer Warranty"), int(p.get("delivery_days", 3)),
            p.get("return_policy", "7 Days Replacement / Return"), now, now
        ))
        return True, "Product added successfully!"

def update_product_admin(product_id, p):
    """Updates an existing product."""
    with get_connection() as conn:
        now = datetime.now().isoformat(timespec="seconds")
        disc = int(round((float(p["original_price"]) - float(p["price"])) / float(p["original_price"]) * 100)) if float(p.get("original_price", 0)) > 0 else 0
        conn.execute("""
            UPDATE products SET
                name = ?, brand = ?, category = ?, subcategory = ?, description = ?,
                price = ?, original_price = ?, discount_percent = ?, stock = ?,
                image_url = ?, specifications = ?, warranty = ?, updated_at = ?
            WHERE id = ?
        """, (
            p["name"].strip(), p["brand"].strip(), p["category"].strip(), p["subcategory"].strip(),
            p.get("description", "").strip(), float(p["price"]), float(p["original_price"]),
            disc, int(p["stock"]), p.get("image_url", "").strip(),
            p.get("specifications", "{}"), p.get("warranty", "1 Year Warranty"),
            now, product_id
        ))
        return True, "Product updated successfully!"

def delete_product_admin(product_id):
    """Deletes or marks product inactive."""
    with get_connection() as conn:
        ordered = conn.execute("SELECT id FROM order_items WHERE product_id = ?", (product_id,)).fetchone()
        if ordered:
            conn.execute("UPDATE products SET status = 'inactive' WHERE id = ?", (product_id,))
            return True, "Product has existing order history; marked as inactive."
        else:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            return True, "Product deleted from catalogue."

def quick_update_stock_admin(product_id, new_stock):
    """Quickly modifies product stock count."""
    with get_connection() as conn:
        conn.execute("UPDATE products SET stock = ? WHERE id = ?", (max(0, int(new_stock)), product_id))

def get_low_stock_products_admin(threshold=5):
    """Returns products where inventory is below or equal to threshold."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM products WHERE stock <= ? AND status = 'active' ORDER BY stock ASC", (threshold,)).fetchall()
        return [dict(r) for r in rows]

def get_all_customers_admin(search=""):
    """Customer administration list with metrics."""
    with get_connection() as conn:
        where = "WHERE role = 'customer'"
        params = []
        if search.strip():
            terms = f"%{search.strip().lower()}%"
            where += " AND (LOWER(name) LIKE ? OR LOWER(email) LIKE ? OR LOWER(phone) LIKE ?)"
            params.extend([terms, terms, terms])

        rows = conn.execute(f"SELECT * FROM users {where} ORDER BY id DESC", params).fetchall()
        customers = [dict(r) for r in rows]
        for c in customers:
            c.pop("password", None)
            c["orders_count"] = conn.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (c["id"],)).fetchone()[0]
            spent = conn.execute("SELECT COALESCE(SUM(total), 0) FROM orders WHERE user_id = ? AND status != 'Cancelled'", (c["id"],)).fetchone()[0]
            c["total_spent"] = float(spent)
        return customers

def toggle_user_active_admin(user_id):
    """Activates or suspends a customer account."""
    with get_connection() as conn:
        user = conn.execute("SELECT is_active FROM users WHERE id = ?", (user_id,)).fetchone()
        if user:
            new_state = 0 if user["is_active"] else 1
            conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_state, user_id))
            return True, f"Customer account {'activated' if new_state else 'suspended'}."
        return False, "Customer not found."

def get_report_data(report_type):
    """Generates structured dataset for export (CSV / Excel)."""
    with get_connection() as conn:
        if report_type == "orders":
            sql = "SELECT id, order_number, user_id, subtotal, discount, coupon_code, delivery_fee, tax_amount, total, payment_method, status, created_at FROM orders ORDER BY id DESC"
        elif report_type == "returns":
            sql = "SELECT id, return_number, order_id, product_id, user_id, quantity, reason, status, refund_method, pickup_date, created_at FROM returns ORDER BY id DESC"
        elif report_type == "products":
            sql = "SELECT id, sku, name, brand, category, subcategory, price, stock, rating, review_count, status FROM products ORDER BY id ASC"
        elif report_type == "customers":
            sql = "SELECT id, name, email, phone, role, is_active, created_at FROM users WHERE role = 'customer' ORDER BY id ASC"
        else:
            sql = "SELECT * FROM refunds ORDER BY id DESC"
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]
