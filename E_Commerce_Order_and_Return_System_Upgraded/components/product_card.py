import html
import streamlit as st
from utils.helpers import money, stars, generate_image_svg

def render_product_card(product: dict, user: dict = None, is_wishlisted: bool = False, key_suffix: str = ""):
    """Renders a responsive, professional e-commerce product card with actions."""
    if not isinstance(product, dict):
        return

    pid = product.get("id", 0)
    pname = str(product.get("name", "Product"))
    brand = str(product.get("brand", ""))
    cat_name = str(product.get("category", "General"))

    # Robust price & stock parsing
    try:
        price = float(product.get("price", 0.0))
    except (ValueError, TypeError):
        price = 0.0

    try:
        orig_price = float(product.get("original_price", price))
    except (ValueError, TypeError):
        orig_price = price

    try:
        discount = int(product.get("discount_percent", 0))
    except (ValueError, TypeError):
        discount = 0

    try:
        stock = int(product.get("stock", 0))
    except (ValueError, TypeError):
        stock = 0

    try:
        rating = float(product.get("rating", 4.5))
    except (ValueError, TypeError):
        rating = 4.5

    # Robust reviews count extraction (supports review_count, reviews, reviews_count, rating_count)
    reviews_raw = product.get("review_count")
    if reviews_raw is None:
        reviews_raw = product.get("reviews")
    if reviews_raw is None:
        reviews_raw = product.get("reviews_count")
    if reviews_raw is None:
        reviews_raw = product.get("rating_count", 0)

    try:
        reviews_count = int(reviews_raw) if reviews_raw is not None else 0
    except (ValueError, TypeError):
        reviews_count = 0

    # Robust, graceful image fallback handling
    raw_img = product.get("image_url", "").strip() if product.get("image_url") else ""
    fallback_img = generate_image_svg(cat_name, pname)

    # HTML Escaped strings for XSS prevention
    escaped_brand = html.escape(brand)
    escaped_cat = html.escape(cat_name)
    escaped_name = html.escape(pname)

    with st.container(border=True):
        # Render image with graceful fallback protection (using width='stretch' to avoid deprecation warnings)
        if raw_img and (raw_img.startswith("http://") or raw_img.startswith("https://") or raw_img.startswith("data:image/")):
            try:
                st.image(raw_img, width="stretch")
            except Exception:
                st.image(fallback_img, width="stretch")
        else:
            st.image(fallback_img, width="stretch")

        # Brand and Category
        st.markdown(f'<div class="prod-brand">{escaped_brand} · {escaped_cat}</div>', unsafe_allow_html=True)

        # Title
        st.markdown(f'<div class="prod-title" title="{escaped_name}">{escaped_name}</div>', unsafe_allow_html=True)

        # Rating and Reviews
        reviews_badge = f"({reviews_count:,} reviews)" if reviews_count > 0 else "(No reviews yet)"
        st.markdown(f"""
        <div class="prod-rating">
            <span>★ {rating:.1f}</span>
            <span>{reviews_badge}</span>
        </div>
        """, unsafe_allow_html=True)

        # Pricing
        orig_html = f'<span class="prod-orig-price">{money(orig_price)}</span>' if orig_price > price else ''
        disc_html = f'<span class="prod-discount">{discount}% OFF</span>' if discount > 0 else ''
        st.markdown(f"""
        <div class="prod-price-row">
            <span class="prod-price">{money(price)}</span>
            {orig_html}
            {disc_html}
        </div>
        """, unsafe_allow_html=True)

        # Stock status
        if stock <= 0:
            st.markdown('<div class="badge-low-stock" style="color:#dc2626;">✕ Out of Stock</div>', unsafe_allow_html=True)
        elif stock <= 5:
            st.markdown(f'<div class="badge-low-stock">⚠ Only {stock} left in stock</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="badge-stock">✓ In Stock</div>', unsafe_allow_html=True)

        # Action Buttons
        b1, b2 = st.columns([1, 1.2])

        # Wishlist toggle
        heart_label = "❤️ Saved" if is_wishlisted else "🤍 Wishlist"
        if b1.button(heart_label, key=f"wish_{pid}_{key_suffix}", use_container_width=True):
            if "wishlist" not in st.session_state:
                st.session_state.wishlist = set()
            if pid in st.session_state.wishlist:
                st.session_state.wishlist.remove(pid)
                if user:
                    from database.repository import toggle_wishlist
                    toggle_wishlist(user["id"], pid)
                st.toast(f"Removed '{pname[:20]}' from wishlist")
            else:
                st.session_state.wishlist.add(pid)
                if user:
                    from database.repository import toggle_wishlist
                    toggle_wishlist(user["id"], pid)
                st.toast(f"Added '{pname[:20]}' to wishlist ❤️")
            st.rerun()

        # Add to cart
        if b2.button("Add to Cart", key=f"cart_{pid}_{key_suffix}", disabled=(stock <= 0), type="primary", use_container_width=True):
            if "cart" not in st.session_state:
                st.session_state.cart = {}
            st.session_state.cart[pid] = st.session_state.cart.get(pid, 0) + 1
            st.toast(f"Added to Cart: {pname[:25]}... 🛒")
            st.rerun()

        # View details button
        if st.button("View Details", key=f"details_{pid}_{key_suffix}", use_container_width=True):
            st.session_state.selected_product_id = pid
            st.session_state.nav_page = "product_details"
            st.rerun()
