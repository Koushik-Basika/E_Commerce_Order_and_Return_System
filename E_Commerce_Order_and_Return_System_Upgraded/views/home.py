import streamlit as st
from database.repository import get_curated_products, get_categories
from components.product_card import render_product_card

def render_home_page(user: dict):
    """Renders the e-commerce homepage with hero banner, category carousels, and curated product showcases."""
    
    # Hero Section
    st.markdown("""
    <div class="brand-hero">
        <h1>E-Commerce Order and Return System</h1>
        <p>Everything you need. One seamless shopping experience. Browse 750+ authentic products with lightning-fast delivery and a transparent 7-day return guarantee.</p>
    </div>
    """, unsafe_allow_html=True)

    # Hero CTA buttons
    c1, c2, c3 = st.columns([1.5, 1.5, 4])
    with c1:
        if st.button("🛍️ Shop Now", type="primary", use_container_width=True):
            st.session_state.nav_page = "shop"
            st.rerun()
    with c2:
        if st.button("⚡ Explore Deals", use_container_width=True):
            st.session_state.nav_page = "deals"
            st.rerun()

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # 2. Main Dashboard Search Console (Clearly Visible & Functional)
    with st.container(border=True):
        st.markdown("""
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
            <span style="font-size:1.2rem;">🔍</span>
            <span style="font-size:1.1rem; font-weight:800; color:#0f172a;">Search Catalogue, Brands, Categories & Orders</span>
        </div>
        """, unsafe_allow_html=True)

        h_search_query = st.session_state.get("search_query", "")

        if h_search_query:
            sc1, sc2, sc3 = st.columns([5.5, 1.2, 1.0])
            with sc3:
                if st.button("✕ Clear", key="btn_dash_clear", use_container_width=True):
                    st.session_state.search_query = ""
                    st.session_state.order_search_query = ""
                    st.session_state.shop_page_num = 1
                    st.rerun()
        else:
            sc1, sc2 = st.columns([5.8, 1.2])

        with sc1:
            dash_q = st.text_input(
                "Dashboard Search Input",
                value=h_search_query,
                placeholder="Search products, categories, brands, SKUs, or order numbers...",
                label_visibility="collapsed",
                key="dash_home_search_input"
            )

        with sc2:
            dash_search_clicked = st.button("Search", key="btn_dash_search_submit", type="primary", use_container_width=True)

        if (dash_search_clicked or (dash_q != h_search_query and dash_q.strip())) and (dash_q.strip() or h_search_query):
            q_clean = dash_q.strip()
            if q_clean.upper().startswith("ORD-") or q_clean.upper().startswith("#ORD-"):
                st.session_state.order_search_query = q_clean.lstrip("#").strip()
                st.session_state.nav_page = "orders"
                st.rerun()
            else:
                st.session_state.search_query = q_clean
                st.session_state.filter_category = "All"
                st.session_state.nav_page = "shop"
                st.session_state.shop_page_num = 1
                st.rerun()

        # Popular Quick Searches
        st.markdown("<div style='font-size:0.8rem; color:#64748b; font-weight:600; margin-top:4px;'>Popular Quick Searches:</div>", unsafe_allow_html=True)
        chip_cols = st.columns(6)
        chips = [
            ("📱 Mobiles", "Mobiles"),
            ("💻 Laptops", "Laptops"),
            ("🎧 Electronics", "Electronics"),
            ("👗 Fashion", "Fashion"),
            ("👟 Footwear", "Footwear"),
            ("🍳 Kitchen", "Home & Kitchen")
        ]
        for idx, (label, cat_filter) in enumerate(chips):
            with chip_cols[idx]:
                if st.button(label, key=f"dash_chip_{idx}", use_container_width=True):
                    st.session_state.filter_category = cat_filter
                    st.session_state.search_query = ""
                    st.session_state.nav_page = "shop"
                    st.session_state.shop_page_num = 1
                    st.rerun()

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # Feature Highlights Bar
    with st.container(border=True):
        f1, f2, f3, f4 = st.columns(4)
        f1.markdown("🚀 **Free Delivery**  \nOn all orders above ₹999")
        f2.markdown("↩️ **7-Day Returns**  \nInstant pickup & full refund")
        f3.markdown("🛡️ **100% Authentic**  \nDirect from verified brands")
        f4.markdown("💳 **Flexible Payments**  \nUPI, Cards, NetBanking & COD")

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # Category Highlights Row
    st.markdown("### 🏷️ Explore Popular Categories")
    categories = get_categories()[:6]
    cat_cols = st.columns(len(categories))
    for i, cat in enumerate(categories):
        with cat_cols[i]:
            with st.container(border=True):
                st.markdown(f"""
                <div style="text-align:center;">
                    <div style="font-size:2rem; margin-bottom:4px;">{cat.get('icon', '🛍️')}</div>
                    <div style="font-weight:700; font-size:0.95rem; color:#0f172a;">{cat['name']}</div>
                    <div style="font-size:0.75rem; color:#64748b;">{cat.get('product_count', 0)} Items</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Browse", key=f"cat_home_{cat['id']}", use_container_width=True):
                    st.session_state.filter_category = cat["name"]
                    st.session_state.nav_page = "shop"
                    st.rerun()

    wishlist_ids = st.session_state.get("wishlist", set())

    # 1. Trending Products Section
    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("### 🔥 Trending Products")
    st.caption("Top trending customer picks this week")
    trending = get_curated_products("trending", limit=4)
    t_cols = st.columns(4)
    for i, p in enumerate(trending):
        with t_cols[i]:
            render_product_card(p, user, is_wishlisted=(p["id"] in wishlist_ids), key_suffix=f"trend_{i}")

    # 2. Today's Deals Section
    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("### ⚡ Today's Flash Deals")
    st.caption("Massive discounts up to 50% off for a limited time")
    deals = get_curated_products("deals", limit=4)
    d_cols = st.columns(4)
    for i, p in enumerate(deals):
        with d_cols[i]:
            render_product_card(p, user, is_wishlisted=(p["id"] in wishlist_ids), key_suffix=f"deal_{i}")

    # 3. Best Sellers Section
    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("### 🏆 Best Sellers")
    st.caption("The most loved items based on verified purchases")
    bestsellers = get_curated_products("bestsellers", limit=4)
    b_cols = st.columns(4)
    for i, p in enumerate(bestsellers):
        with b_cols[i]:
            render_product_card(p, user, is_wishlisted=(p["id"] in wishlist_ids), key_suffix=f"best_{i}")

    # 4. Top Rated Products Section
    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("### ⭐ Top Rated Products")
    st.caption("Highest rated items by our community")
    top_rated = get_curated_products("top_rated", limit=4)
    r_cols = st.columns(4)
    for i, p in enumerate(top_rated):
        with r_cols[i]:
            render_product_card(p, user, is_wishlisted=(p["id"] in wishlist_ids), key_suffix=f"top_{i}")

    # 5. New Arrivals Section
    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("### ✨ New Arrivals")
    st.caption("Fresh items added to our catalogue recently")
    new_arrivals = get_curated_products("new_arrivals", limit=4)
    n_cols = st.columns(4)
    for i, p in enumerate(new_arrivals):
        with n_cols[i]:
            render_product_card(p, user, is_wishlisted=(p["id"] in wishlist_ids), key_suffix=f"new_{i}")
