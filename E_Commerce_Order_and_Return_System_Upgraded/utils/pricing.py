"""
E-Commerce Order and Return System — Centralized Server-Side Pricing & Tax Engine
Handles verified subtotal calculations, coupon validations, shipping computation,
GST tax accounting (inclusive), and partial refund determinations.
"""

from datetime import datetime

# Standard tax rate across catalogue (18% GST inclusive)
GST_RATE = 0.18

def calculate_order_pricing(conn, cart_dict: dict, coupon_code: str = "", delivery_method: str = "Standard") -> dict:
    """
    Trusted server-side pricing recalculation.
    Never trusts client-submitted subtotals, discounts, or delivery fees.
    
    Returns dict with verified calculations or raises/returns error status.
    """
    if not cart_dict:
        return {"valid": False, "error": "Cart is empty."}

    subtotal = 0.0
    verified_items = []

    for pid, qty in cart_dict.items():
        qty = int(qty)
        if qty <= 0:
            return {"valid": False, "error": f"Invalid quantity {qty} for product #{pid}."}

        p = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if not p:
            return {"valid": False, "error": f"Product #{pid} not found in catalogue."}
        if p["status"] != "active":
            return {"valid": False, "error": f"Product '{p['name']}' is no longer active."}
        if p["stock"] < qty:
            return {"valid": False, "error": f"Insufficient stock for '{p['name']}'. Only {p['stock']} available."}

        unit_price = float(p["price"])
        item_total = round(unit_price * qty, 2)
        subtotal = round(subtotal + item_total, 2)

        verified_items.append({
            "product_id": p["id"],
            "name": p["name"],
            "brand": p["brand"],
            "image_url": p["image_url"],
            "unit_price": unit_price,
            "quantity": qty,
            "total_price": item_total,
            "stock_available": p["stock"]
        })

    # Coupon Validation
    discount = 0.0
    validated_coupon_code = None

    if coupon_code and coupon_code.strip():
        code_clean = coupon_code.strip().upper()
        now_str = datetime.now().strftime("%Y-%m-%d")
        cp = conn.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code_clean,)).fetchone()

        if cp:
            # Check expiration
            if cp["expiry_date"] and cp["expiry_date"] < now_str:
                pass  # Expired, ignore discount
            # Check usage limit
            elif cp["usage_limit"] and cp["times_used"] >= cp["usage_limit"]:
                pass  # Limit reached, ignore
            # Check minimum order amount
            elif subtotal < float(cp["min_order_amount"]):
                pass  # Order amount threshold not met
            else:
                validated_coupon_code = code_clean
                disc_val = float(cp["discount_value"])
                if cp["discount_type"] == "percent":
                    calc_disc = subtotal * (disc_val / 100.0)
                    discount = min(calc_disc, float(cp["max_discount"]))
                else:
                    discount = min(disc_val, subtotal)
                discount = round(discount, 2)

    # Delivery Fee Calculation
    is_express = (str(delivery_method).strip().lower() == "express")
    discounted_subtotal = max(0.0, subtotal - discount)
    if is_express:
        delivery_fee = 99.0
    else:
        delivery_fee = 0.0 if discounted_subtotal >= 999.0 else 49.0

    # Tax calculation: GST 18% is inclusive in catalog price to prevent double taxation
    # Taxable base = Amount / (1 + GST_RATE)
    # GST Amount = Amount - Taxable base
    taxable_amount = discounted_subtotal / (1.0 + GST_RATE)
    tax_amount = round(discounted_subtotal - taxable_amount, 2)

    total = round(max(0.0, discounted_subtotal + delivery_fee), 2)

    return {
        "valid": True,
        "items": verified_items,
        "subtotal": subtotal,
        "coupon_code": validated_coupon_code,
        "discount": discount,
        "delivery_method": "Express" if is_express else "Standard",
        "delivery_fee": delivery_fee,
        "tax_amount": tax_amount,
        "total": total
    }

def calculate_item_refund_amount(order_item_price: float, return_qty: int, order_subtotal: float = 0.0, order_discount: float = 0.0) -> float:
    """
    Computes fair refund amount for returned items.
    If an order-level discount was applied, the refund reflects the net amount paid for those items.
    """
    gross_item_total = float(order_item_price) * int(return_qty)
    if order_subtotal > 0 and order_discount > 0:
        discount_ratio = min(1.0, max(0.0, order_discount / order_subtotal))
        net_refund = gross_item_total * (1.0 - discount_ratio)
    else:
        net_refund = gross_item_total

    return round(max(0.0, net_refund), 2)

