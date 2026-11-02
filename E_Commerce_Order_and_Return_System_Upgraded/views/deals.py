import streamlit as st
from database.repository import get_active_coupons, get_curated_products
from components.product_card import render_product_card
from utils.helpers import money

def render_deals_page(user: dict):
    """Renders the Deals, Discounts, and Promotional Coupons showcase page."""
    st.markdown("""
    <div class="brand-hero" style="background:linear-gradient(135deg, #7c2d12 0%, #ea580c 50%, #f97316 100%);">
        <h1>⚡ Exclusive Deals & Promo Offers</h1>
        <p>Save big on top electronics, smartphones, apparel, and footwear with limited-time coupons and massive price cuts.</p>
    </div>
    """, unsafe_allow_html=True)

    # Coupons Section
    st.markdown("### 🎟️ Available Discount Coupons")
    st.caption("Apply these coupons during checkout to unlock additional savings:")

    coupons = get_active_coupons()
    c_cols = st.columns(len(coupons))
    for i, c in enumerate(coupons):
        with c_cols[i]:
            with st.container(border=True):
                st.markdown(f"""
                <div style="text-align:center;">
                    <div style="background:#fef3c7; color:#b45309; padding:4px 10px; border-radius:6px; font-weight:800; font-size:1.1rem; border:1px dashed #f59e0b; margin-bottom:8px;">
                        {c['code']}
                    </div>
                    <div style="font-weight:700; color:#0f172a; font-size:0.95rem;">
                        {f"{int(c['discount_value'])}% OFF" if c['discount_type'] == 'percent' else f"FLAT ₹{int(c['discount_value'])} OFF"}
                    </div>
                    <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">
                        Min Order: {money(c['min_order_amount'])}
                    </div>
                    <div style="font-size:0.75rem; color:#64748b;">
                        Max Disc: {money(c['max_discount'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)
                if st.button("Apply Code", key=f"apply_c_{c['code']}", use_container_width=True):
                    st.session_state.coupon_code = c["code"]
                    st.toast(f"Coupon {c['code']} selected! Proceed to Cart or Checkout.")

    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)

    # Super Saver Deals Section
    st.markdown("### 🔥 Super Saver Deals (30%+ OFF)")
    deals_prods = get_curated_products("deals", limit=12)
    wishlist_ids = st.session_state.get("wishlist", set())

    d_cols = st.columns(4)
    for i, p in enumerate(deals_prods):
        with d_cols[i % 4]:
            render_product_card(p, user, is_wishlisted=(p["id"] in wishlist_ids), key_suffix=f"deals_grid_{p['id']}")
