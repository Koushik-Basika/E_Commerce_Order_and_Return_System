import json
import streamlit as st
from database.repository import (
    get_product_by_id,
    get_product_reviews,
    get_product_rating_breakdown,
    is_verified_purchaser,
    add_product_review,
    get_related_products,
    toggle_wishlist
)
from utils.helpers import money, stars, generate_image_svg, format_date
from components.product_card import render_product_card

def render_product_details_page(user: dict):
    """Renders comprehensive product details, specs, verified reviews, and related products."""
    pid = st.session_state.get("selected_product_id")
    if not pid:
        st.warning("No product selected. Returning to Shop.")
        st.session_state.nav_page = "shop"
        st.rerun()
        return

    product = get_product_by_id(pid)
    if not product:
        st.error("Product not found.")
        if st.button("Back to Catalogue"):
            st.session_state.nav_page = "shop"
            st.rerun()
        return

    # Breadcrumb
    b_col1, b_col2 = st.columns([4, 1])
    with b_col1:
        st.caption(f"🏠 Home  /  🛍️ {product.get('category')}  /  {product.get('subcategory')}  /  **{product['name']}**")
    with b_col2:
        if st.button("◀ Back to Catalogue", use_container_width=True):
            st.session_state.nav_page = "shop"
            st.rerun()

    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

    # Main Grid (Left: Image Gallery, Right: Details & Purchase)
    col_img, col_info = st.columns([1.1, 1.4], gap="large")

    with col_img:
        cat_name = product.get("category", "General")
        fallback_img = generate_image_svg(cat_name, product["name"])
        raw_main = product.get("image_url", "").strip() if product.get("image_url") else ""
        main_img = raw_main if (raw_main.startswith("http://") or raw_main.startswith("https://") or raw_main.startswith("data:image/")) else fallback_img

        try:
            st.image(main_img, width="stretch")
        except Exception:
            st.image(fallback_img, width="stretch")

        # Multi-angle / variant gallery thumbnails
        gallery = []
        if product.get("gallery_images"):
            try:
                gallery = json.loads(product["gallery_images"])
            except Exception:
                gallery = []
        if not gallery:
            from utils.image_catalog import get_product_gallery_images
            gallery = get_product_gallery_images(
                cat_name,
                product.get("subcategory", ""),
                main_img,
                product.get("sku", str(product.get("id")))
            )

        # Render 3 distinct thumbnails
        thumb_urls = [main_img] + [u for u in gallery if u != main_img]
        while len(thumb_urls) < 3:
            thumb_urls.append(main_img)
        t1, t2, t3 = st.columns(3)
        with t1:
            try:
                st.image(thumb_urls[0], width="stretch")
            except Exception:
                st.image(fallback_img, width="stretch")
        with t2:
            try:
                st.image(thumb_urls[1], width="stretch")
            except Exception:
                st.image(fallback_img, width="stretch")
        with t3:
            try:
                st.image(thumb_urls[2], width="stretch")
            except Exception:
                st.image(fallback_img, width="stretch")

        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("##### 🛡️ Service & Quality Guarantees")
            st.markdown(f"""
            * 🚚 **Fast Delivery:** {product.get('delivery_days', 3)} Days Express Dispatch
            * ↩️ **Return Window:** {product.get('return_policy', '7 Days Replacement / Return')}
            * 🛡️ **Warranty:** {product.get('warranty', '1 Year Manufacturer Warranty')}
            * 💯 **Genuine:** 100% Original Brand Assured
            """)

    with col_info:
        st.markdown(f'<div class="prod-brand">{product.get("brand")} · {product.get("category")}</div>', unsafe_allow_html=True)
        st.markdown(f"## {product['name']}")

        # Rating and SKU
        r_col1, r_col2 = st.columns([2, 1])
        with r_col1:
            st.markdown(f"⭐ **{product.get('rating', 4.5)}** · ({product.get('review_count', 0):,} verified ratings)")
        with r_col2:
            st.caption(f"SKU: `{product.get('sku')}`")

        st.divider()

        # Pricing
        price = product["price"]
        orig_price = product.get("original_price", price)
        discount = product.get("discount_percent", 0)
        savings = max(0, orig_price - price)

        p_row1, p_row2 = st.columns([2, 2])
        with p_row1:
            st.markdown(f"""
            <div style="display:flex; align-items:baseline; gap:12px;">
                <span style="font-size:2rem; font-weight:800; color:#0f172a;">{money(price)}</span>
                <span style="font-size:1.1rem; color:#94a3b8; text-decoration:line-through;">{money(orig_price)}</span>
                <span style="background:#dcfce7; color:#16a34a; font-weight:700; padding:4px 8px; border-radius:6px; font-size:0.9rem;">{discount}% OFF</span>
            </div>
            """, unsafe_allow_html=True)
            if savings > 0:
                st.caption(f"You save **{money(savings)}** (Inclusive of all taxes)")

        # Stock status
        stock = product.get("stock", 0)
        if stock <= 0:
            st.error("Currently Out of Stock")
        elif stock <= 5:
            st.warning(f"⚠ Hurry! Only {stock} items left in stock.")
        else:
            st.success(f"✓ In Stock ({stock} available)")

        st.divider()

        # Description
        st.markdown("##### About this product")
        st.write(product.get("description", "High quality product from verified manufacturer."))

        # Quantity and Cart controls
        q_col, btn_cart_col, btn_buy_col = st.columns([1, 1.5, 1.5])
        with q_col:
            selected_qty = st.number_input("Qty", min_value=1, max_value=max(1, stock), value=1, disabled=(stock <= 0))
        with btn_cart_col:
            if st.button("Add to Cart", type="secondary", disabled=(stock <= 0), use_container_width=True):
                if "cart" not in st.session_state:
                    st.session_state.cart = {}
                st.session_state.cart[pid] = st.session_state.cart.get(pid, 0) + selected_qty
                st.toast(f"Added {selected_qty}x to Cart! 🛒")
        with btn_buy_col:
            if st.button("⚡ Buy Now", type="primary", disabled=(stock <= 0), use_container_width=True):
                if "cart" not in st.session_state:
                    st.session_state.cart = {}
                st.session_state.cart[pid] = st.session_state.cart.get(pid, 0) + selected_qty
                st.session_state.nav_page = "checkout"
                st.rerun()

        # Wishlist button
        wishlist_ids = st.session_state.get("wishlist", set())
        is_w = pid in wishlist_ids
        w_btn_label = "❤️ Saved in Wishlist" if is_w else "🤍 Add to Wishlist"
        if st.button(w_btn_label, use_container_width=True):
            if is_w:
                st.session_state.wishlist.remove(pid)
                if user:
                    toggle_wishlist(user["id"], pid)
                st.toast("Removed from Wishlist")
            else:
                st.session_state.wishlist.add(pid)
                if user:
                    toggle_wishlist(user["id"], pid)
                st.toast("Added to Wishlist ❤️")
            st.rerun()

    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)

    # Specifications Section
    st.markdown("### 📋 Product Specifications")
    with st.container(border=True):
        try:
            specs = json.loads(product.get("specifications", "{}"))
        except Exception:
            specs = {}

        if not specs:
            specs = {
                "Brand": product.get("brand"),
                "Category": product.get("category"),
                "Subcategory": product.get("subcategory"),
                "Warranty": product.get("warranty", "1 Year"),
                "Model Year": "2026",
                "Country of Origin": "India"
            }

        s_cols = st.columns(2)
        for i, (k, v) in enumerate(specs.items()):
            col = s_cols[i % 2]
            col.markdown(f"**{k}:** {v}")
            col.write("---")

    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)

    # Customer Reviews & Ratings Breakdown
    st.markdown("### 💬 Verified Customer Reviews")
    stats = get_product_rating_breakdown(pid)
    st.write("Debug - Rating statistics:", stats)
    reviews = get_product_reviews(pid)

    rev_col1, rev_col2 = st.columns([1, 2], gap="large")

    with rev_col1:
        with st.container(border=True):
            st.markdown(f"## {stats['average_rating']} ★")
            st.caption(f"Based on {stats['total_reviews']} verified ratings")
            st.divider()

            # Breakdown bars
            for s in range(5, 0, -1):
                pct = stats["distribution"].get(s, 0)
                st.write(f"{s} Star: {pct:.0f}%")
                st.progress(pct / 100.0)

    with rev_col2:
        # Check verified purchase status for review submission
        user_id = user.get("id") if user else None
        can_review = is_verified_purchaser(user_id, pid) if user_id else False

        if can_review:
            with st.expander("✍️ Write a Customer Review", expanded=False):
                with st.form(f"review_form_{pid}"):
                    r_score = st.slider("Rating", 1, 5, 5)
                    r_head = st.text_input("Review Headline", placeholder="e.g. Great product and fast shipping!")
                    r_text = st.text_area("Your Review", placeholder="Share your experience with this item...")
                    if st.form_submit_button("Submit Review", type="primary"):
                        if not r_text.strip():
                            st.warning("Please enter review text.")
                        else:
                            add_product_review(pid, user_id, user.get("name", "Customer"), r_score, r_head, r_text)
                            st.success("Thank you! Your verified review has been published.")
                            st.rerun()
        else:
            if user:
                st.caption("ℹ️ Only verified customers who purchased and received this product can submit a review.")

        # Review List
        if reviews:
            for r in reviews:
                with st.container(border=True):
                    rc1, rc2 = st.columns([3, 1])
                    with rc1:
                        st.markdown(f"**{stars(r['rating'])} {r.get('headline', '')}**")
                        st.write(r.get("comment", ""))
                        st.caption(f"By **{r.get('user_name', 'Customer')}** · ✓ Verified Purchase · {format_date(r.get('created_at', ''))}")
                    with rc2:
                        st.markdown('<span style="color:#16a34a; font-size:0.8rem; font-weight:700;">✓ Verified</span>', unsafe_allow_html=True)
        else:
            st.info("No customer reviews yet. Be the first verified customer to review this product!")

    st.markdown("<div style='margin-top:3rem;'></div>", unsafe_allow_html=True)

    # Related Products Section ("You May Also Like" & "Customers Also Bought")
    st.markdown("### 💡 You May Also Like")
    st.caption(f"Popular recommendations in {product.get('category')}")
    related = get_related_products(pid, product.get("category"), product.get("brand"), limit=4)
    rel_cols = st.columns(4)
    for i, p in enumerate(related):
        with rel_cols[i]:
            render_product_card(p, user, is_wishlisted=(p["id"] in wishlist_ids), key_suffix=f"rel_{p['id']}")
