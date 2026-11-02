import html
import streamlit as st
from database.repository import (
    get_products_paginated,
    get_categories,
    get_subcategories,
    get_brands,
    get_price_bounds
)
from components.product_card import render_product_card

def render_shop_page(user: dict):
    """Renders the product catalogue with server-side pagination, search, multi-filters, and sorting."""
    st.markdown("""
    <div class="section-banner">
        <h2>🛍️ Product Catalogue</h2>
        <p>Browse our extensive collection of 750+ genuine products with dynamic search and filters.</p>
    </div>
    """, unsafe_allow_html=True)

    # Search Bar with Clear Option
    active_search = st.session_state.get("search_query", "")

    if active_search:
        s_col1, s_col_clear, s_col2 = st.columns([3.8, 1.0, 1.4])
        with s_col_clear:
            if st.button("✕ Clear Search", key="btn_shop_clear_search", use_container_width=True):
                st.session_state.search_query = ""
                st.session_state.shop_page_num = 1
                st.rerun()
    else:
        s_col1, s_col2 = st.columns([4.2, 1.4])

    with s_col1:
        search_input_val = st.text_input(
            "Search",
            value=active_search,
            placeholder="🔍 Search for products, brands, categories, specifications, or SKU...",
            label_visibility="collapsed",
            key="shop_search_input_field"
        )
        if search_input_val != active_search:
            st.session_state.search_query = search_input_val.strip()
            st.session_state.shop_page_num = 1
            st.rerun()

    with s_col2:
        sort_by = st.selectbox(
            "Sort by",
            [
                "Relevance",
                "Popularity",
                "Price: Low to High",
                "Price: High to Low",
                "Rating",
                "Newest",
                "Biggest Discount",
                "Most Reviewed"
            ],
            label_visibility="collapsed"
        )

    # Active search badge indicator
    if active_search:
        st.markdown(f"""
        <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; padding:6px 14px; margin-bottom:10px; display:flex; align-items:center; gap:8px;">
            <span style="font-weight:700; color:#1d4ed8; font-size:0.88rem;">🔍 Search Results:</span>
            <span style="font-weight:600; color:#1e293b; font-size:0.88rem;">"{html.escape(active_search)}"</span>
        </div>
        """, unsafe_allow_html=True)

    # Filters Section in an Expander or Sidebar-style columns
    with st.expander("⚙️ Advanced Filters & Refinements", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        # Category Filter
        cats = ["All"] + [c["name"] for c in get_categories()]
        current_cat = st.session_state.get("filter_category", "All")
        cat_idx = cats.index(current_cat) if current_cat in cats else 0
        with f_col1:
            sel_category = st.selectbox("Category", cats, index=cat_idx)
            st.session_state.filter_category = sel_category

        # Subcategory Filter
        subcats = ["All"] + get_subcategories(sel_category)
        with f_col2:
            sel_subcategory = st.selectbox("Subcategory", subcats)

        # Brand Filter
        brands = ["All"] + get_brands(sel_category)
        with f_col3:
            sel_brand = st.selectbox("Brand", brands)

        # Rating & Stock Filters
        with f_col4:
            sel_rating = st.selectbox("Customer Rating", [
                "Any Rating", "4★ & above", "3★ & above", "2★ & above"
            ])
            min_rating_val = 4.0 if "4" in sel_rating else (3.0 if "3" in sel_rating else (2.0 if "2" in sel_rating else 0.0))

        f2_col1, f2_col2, f2_col3 = st.columns([2, 1.5, 1.5])
        with f2_col1:
            min_bound, max_bound = get_price_bounds(sel_category)
            price_range = st.slider("Price Range (₹)", min_value=int(min_bound), max_value=int(max_bound), value=(int(min_bound), int(max_bound)), step=100)
        with f2_col2:
            sel_discount = st.selectbox("Minimum Discount", ["All Discounts", "10%+ Off", "20%+ Off", "30%+ Off", "50%+ Off"])
            min_disc_val = 50 if "50" in sel_discount else (30 if "30" in sel_discount else (20 if "20" in sel_discount else (10 if "10" in sel_discount else 0)))
        with f2_col3:
            in_stock_only = st.checkbox("In Stock Only", value=False)
            if st.button("Reset All Filters", use_container_width=True):
                st.session_state.filter_category = "All"
                st.session_state.search_query = ""
                st.session_state.shop_page_num = 1
                st.rerun()

    # Current Page Tracking
    current_page = st.session_state.get("shop_page_num", 1)
    per_page = 24

    # Query Data
    result = get_products_paginated(
        search=active_search,
        category=sel_category,
        subcategory=sel_subcategory,
        brand=sel_brand,
        min_price=price_range[0],
        max_price=price_range[1],
        min_rating=min_rating_val,
        min_discount=min_disc_val,
        in_stock_only=in_stock_only,
        sort_by=sort_by,
        page=current_page,
        per_page=per_page
    )

    items = result["items"]
    total_count = result["total_count"]
    total_pages = result["total_pages"]
    current_page = min(current_page, total_pages)

    # Header Bar: Showing X-Y of Z Products
    start_idx = (current_page - 1) * per_page + 1 if total_count > 0 else 0
    end_idx = min(current_page * per_page, total_count)

    info_c1, info_c2 = st.columns([3, 2])
    with info_c1:
        st.markdown(f"**Showing {start_idx}–{end_idx} of {total_count:,} products**")
    with info_c2:
        st.caption(f"Page {current_page} of {total_pages}")

    st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

    # Empty State Check
    if not items:
        with st.container(border=True):
            st.markdown(f"""
            <div style="text-align:center; padding:2rem 1rem;">
                <div style="font-size:3rem; margin-bottom:0.5rem;">🔍</div>
                <h3 style="color:#0f172a; margin-bottom:0.4rem;">No matching products found</h3>
                <p style="color:#64748b; max-width:520px; margin:0 auto 1.5rem auto; font-size:0.95rem;">
                    We couldn't find any products matching <strong>"{html.escape(active_search or sel_category)}"</strong>.
                    Try checking your spelling, using broader search terms, or resetting your filters.
                </p>
            </div>
            """, unsafe_allow_html=True)
            r_c1, r_c2, r_c3 = st.columns([1.5, 2, 1.5])
            with r_c2:
                if st.button("Reset Search & All Filters", type="primary", use_container_width=True):
                    st.session_state.search_query = ""
                    st.session_state.filter_category = "All"
                    st.session_state.shop_page_num = 1
                    st.rerun()
        return

    # Render 4-column product grid with visible page image deduplication protection
    wishlist_ids = st.session_state.get("wishlist", set())
    seen_page_images = set()
    display_items = []

    for product in items:
        p_copy = dict(product)
        cur_img = p_copy.get("image_url")
        if cur_img and cur_img in seen_page_images:
            from utils.image_catalog import get_images_for_subcategory, get_images_for_category
            pool = get_images_for_subcategory(p_copy.get("category", ""), p_copy.get("subcategory", ""))
            if not pool or len(pool) < 2:
                pool = get_images_for_category(p_copy.get("category", ""))
            for alt in pool:
                if alt["url"] not in seen_page_images:
                    p_copy["image_url"] = alt["url"]
                    break
        if p_copy.get("image_url"):
            seen_page_images.add(p_copy["image_url"])
        display_items.append(p_copy)

    cols = st.columns(4)
    for i, product in enumerate(display_items):
        with cols[i % 4]:
            render_product_card(product, user, is_wishlisted=(product["id"] in wishlist_ids), key_suffix=f"shop_{product['id']}")

    st.divider()

    # Pagination Navigation Controls (< Previous 1 2 3 4 ... Next >)
    p_col1, p_col2, p_col3 = st.columns([1.5, 3, 1.5])

    with p_col1:
        if st.button("◀ Previous Page", disabled=(current_page <= 1), use_container_width=True):
            st.session_state.shop_page_num = current_page - 1
            st.rerun()

    with p_col2:
        # Page selector dropdown
        page_options = list(range(1, total_pages + 1))
        sel_p = st.selectbox(
            "Jump to Page",
            page_options,
            index=(current_page - 1),
            key="jump_page_select",
            label_visibility="collapsed"
        )
        if sel_p != current_page:
            st.session_state.shop_page_num = sel_p
            st.rerun()

    with p_col3:
        if st.button("Next Page ▶", disabled=(current_page >= total_pages), use_container_width=True):
            st.session_state.shop_page_num = current_page + 1
            st.rerun()
