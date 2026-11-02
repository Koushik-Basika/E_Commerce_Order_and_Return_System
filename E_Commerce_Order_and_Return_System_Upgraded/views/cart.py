import streamlit as st
from database.repository import get_product_by_id, validate_coupon
from utils.helpers import money, generate_image_svg

def render_cart_page(user: dict):
    """Renders the shopping cart with quantity modifications, promo codes, and pricing breakdown."""
    st.markdown("""
    <div class="section-banner">
        <h2>🛒 Shopping Cart</h2>
        <p>Review selected items, apply discount promo coupons, and proceed to secure checkout.</p>
    </div>
    """, unsafe_allow_html=True)

    cart = st.session_state.get("cart", {})
    if not cart:
        st.info("Your shopping cart is empty.")
        if st.button("Explore Catalogue", type="primary"):
            st.session_state.nav_page = "shop"
            st.rerun()
        return

    col_items, col_summary = st.columns([1.8, 1.2], gap="large")

    subtotal = 0.0
    items_to_render = []

    with col_items:
        st.markdown(f"**Items in Cart ({sum(cart.values())})**")
        st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

        for pid, qty in list(cart.items()):
            p = get_product_by_id(pid)
            if not p:
                continue

            line_total = p["price"] * qty
            subtotal += line_total
            items_to_render.append((p, qty, line_total))

            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 3.5, 1.5, 1.5])
                with c1:
                    fallback_svg = generate_image_svg(p.get("category", "General"), p["name"])
                    img = p.get("image_url", "").strip() if p.get("image_url") else ""
                    if img and (img.startswith("http://") or img.startswith("https://") or img.startswith("data:image/")):
                        try:
                            st.image(img, width=80)
                        except Exception:
                            st.image(fallback_svg, width=80)
                    else:
                        st.image(fallback_svg, width=80)
                with c2:
                    st.markdown(f"**{p['name']}**")
                    st.caption(f"Brand: {p.get('brand')} | Unit: {money(p['price'])}")
                    if p.get("stock", 0) < qty:
                        st.error(f"Only {p['stock']} left in stock!")
                with c3:
                    new_q = st.number_input(
                        "Qty",
                        min_value=1,
                        max_value=max(1, p.get("stock", 10)),
                        value=min(qty, max(1, p.get("stock", 10))),
                        key=f"cart_qty_{pid}"
                    )
                    if new_q != qty:
                        st.session_state.cart[pid] = new_q
                        st.rerun()
                with c4:
                    st.markdown(f"**{money(line_total)}**")
                    if st.button("Remove", key=f"cart_del_{pid}"):
                        del st.session_state.cart[pid]
                        st.rerun()

    with col_summary:
        with st.container(border=True):
            st.markdown("### Order Summary")
            st.write("---")

            # Promo Code Input
            st.markdown("##### 🎟️ Have a Promo Code?")
            coupon_input = st.text_input(
                "Coupon Code",
                value=st.session_state.get("coupon_code", ""),
                placeholder="e.g. WELCOME10 or SAVE200",
                label_visibility="collapsed"
            )

            coupon_discount = 0.0
            applied_code = ""

            if st.button("Apply Coupon", use_container_width=True):
                if coupon_input.strip():
                    res = validate_coupon(coupon_input, subtotal)
                    if res["valid"]:
                        st.session_state.coupon_code = res["code"]
                        st.session_state.coupon_discount = res["discount"]
                        st.success(res["message"])
                    else:
                        st.session_state.coupon_code = ""
                        st.session_state.coupon_discount = 0.0
                        st.error(res["message"])
                else:
                    st.session_state.coupon_code = ""
                    st.session_state.coupon_discount = 0.0
                st.rerun()

            # Active coupon
            if st.session_state.get("coupon_code"):
                res = validate_coupon(st.session_state["coupon_code"], subtotal)
                if res["valid"]:
                    coupon_discount = res["discount"]
                    applied_code = res["code"]
                    st.caption(f"✅ Applied: **{applied_code}** (- {money(coupon_discount)})")
                else:
                    st.session_state.coupon_code = ""
                    st.session_state.coupon_discount = 0.0

            # Quick Coupon Buttons
            st.caption("Available quick coupons:")
            q1, q2 = st.columns(2)
            if q1.button("WELCOME10 (10%)", use_container_width=True):
                st.session_state.coupon_code = "WELCOME10"
                st.rerun()
            if q2.button("SAVE200 (₹200)", use_container_width=True):
                st.session_state.coupon_code = "SAVE200"
                st.rerun()

            st.write("---")

            # Pricing Calculations
            delivery_fee = 0.0 if subtotal >= 999 else 49.0
            tax_est = round((subtotal - coupon_discount) * 0.18 / 1.18, 2)
            grand_total = max(0.0, subtotal - coupon_discount + delivery_fee)

            st.write(f"Subtotal: **{money(subtotal)}**")
            if coupon_discount > 0:
                st.write(f"Coupon Savings: <span style='color:#16a34a; font-weight:700;'>- {money(coupon_discount)}</span>", unsafe_allow_html=True)
            st.write(f"Estimated GST (18% included): **{money(tax_est)}**")
            st.write(f"Delivery Charges: **{'FREE' if delivery_fee == 0 else money(delivery_fee)}**")
            if subtotal < 999:
                st.caption(f"💡 Add {money(999 - subtotal)} more to get FREE Delivery!")

            st.markdown("---")
            st.markdown(f"## Total: <span style='color:#2563eb;'>{money(grand_total)}</span>", unsafe_allow_html=True)

            # Proceed Button
            if st.button("Proceed to Checkout 💳", type="primary", use_container_width=True):
                st.session_state.nav_page = "checkout"
                st.rerun()

            if st.button("Continue Shopping", use_container_width=True):
                st.session_state.nav_page = "shop"
                st.rerun()
