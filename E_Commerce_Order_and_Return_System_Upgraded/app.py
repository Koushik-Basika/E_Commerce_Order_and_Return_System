import streamlit as st
import database
from components.styles import get_custom_css
from components.navbar import render_navbar
from views import (
    render_auth_page,
    render_home_page,
    render_shop_page,
    render_product_details_page,
    render_categories_page,
    render_deals_page,
    render_wishlist_page,
    render_cart_page,
    render_checkout_page,
    render_orders_page,
    render_returns_page,
    render_profile_page,
    render_admin_page
)

# 1. Page Configuration
st.set_page_config(
    page_title="E-Commerce Order and Return System",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Database Initialization
database.create_schema()
database.seed_database()

# 3. Apply Professional Styling
st.markdown(get_custom_css(), unsafe_allow_html=True)

# 4. Session State Initialization
def init_session():
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("cart", {})
    st.session_state.setdefault("wishlist", set())
    st.session_state.setdefault("coupon_code", "")
    st.session_state.setdefault("coupon_discount", 0.0)
    st.session_state.setdefault("nav_page", "home")
    st.session_state.setdefault("selected_product_id", None)
    st.session_state.setdefault("search_query", "")
    st.session_state.setdefault("filter_category", "All")
    st.session_state.setdefault("shop_page_num", 1)

init_session()

user = st.session_state.get("user")

# 5. Routing Logic
if not user:
    render_auth_page()
else:
    # Top Navigation Bar
    render_navbar(user)

    page = st.session_state.get("nav_page", "home")

    if page == "home":
        render_home_page(user)
    elif page == "shop":
        render_shop_page(user)
    elif page == "product_details":
        render_product_details_page(user)
    elif page == "categories":
        render_categories_page()
    elif page == "deals":
        render_deals_page(user)
    elif page == "wishlist":
        render_wishlist_page(user)
    elif page == "cart":
        render_cart_page(user)
    elif page == "checkout":
        render_checkout_page(user)
    elif page == "orders":
        render_orders_page(user)
    elif page == "returns":
        render_returns_page(user)
    elif page == "profile":
        render_profile_page(user)
    elif page == "admin":
        if user.get("role") == "admin":
            render_admin_page(user)
        else:
            st.error("Access Denied: Administrator credentials required.")
            st.session_state.nav_page = "home"
            st.rerun()
    else:
        render_home_page(user)

# 6. Global Professional Footer
st.markdown("""
<div class="app-footer">
    <strong>E-Commerce Order and Return System</strong><br>
    Enterprise Order Processing, Verified Return Logistics & Real-Time Fulfillment.<br>
    © 2026 E-Commerce Order and Return System. All rights reserved.
</div>
""", unsafe_allow_html=True)
