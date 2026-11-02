import streamlit as st
from database.repository import get_product_by_id, toggle_wishlist
from utils.helpers import money, stars, generate_image_svg

def render_wishlist_page(user: dict):
    """Renders user's saved wishlist items with move-to-cart and remove actions."""
    st.markdown("""
    <div class="section-banner">
        <h2>❤️ My Saved Wishlist</h2>
        <p>Keep track of your favorite items and transfer them to your cart when ready to purchase.</p>
    </div>
    """, unsafe_allow_html=True)

    wishlist_ids = list(st.session_state.get("wishlist", set()))
    user_id = user.get("id") if user else None

    if not wishlist_ids:
        st.info("Your wishlist is currently empty. Explore our catalogue to save products you love!")
        if st.button("Browse Products", type="primary"):
            st.session_state.nav_page = "shop"
            st.rerun()
        return

    st.markdown(f"**{len(wishlist_ids)} items saved**")
    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

    for pid in wishlist_ids:
        p = get_product_by_id(pid)
        if not p:
            continue

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1, 4, 2, 2])
            with c1:
                fallback_svg = generate_image_svg(p.get("category", "General"), p["name"])
                img_url = p.get("image_url", "").strip() if p.get("image_url") else ""
                if img_url and (img_url.startswith("http://") or img_url.startswith("https://") or img_url.startswith("data:image/")):
                    try:
                        st.image(img_url, width=95)
                    except Exception:
                        st.image(fallback_svg, width=95)
                else:
                    st.image(fallback_svg, width=95)
            with c2:
                st.markdown(f"### {p['name']}")
                st.caption(f"Brand: {p.get('brand')} · Category: {p.get('category')}")
                st.write(f"⭐ {p.get('rating', 4.5)} ({p.get('review_count', 0):,} reviews)")
            with c3:
                st.markdown(f"**{money(p['price'])}**")
                if p.get("original_price", 0) > p["price"]:
                    st.caption(f"~~{money(p['original_price'])}~~ · {p.get('discount_percent')}% OFF")
                if p.get("stock", 0) > 0:
                    st.markdown('<span style="color:#16a34a; font-size:0.85rem; font-weight:600;">✓ In Stock</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span style="color:#dc2626; font-size:0.85rem; font-weight:600;">✕ Out of Stock</span>', unsafe_allow_html=True)
            with c4:
                if st.button("🛒 Move to Cart", key=f"w_move_{pid}", disabled=(p.get("stock", 0) <= 0), type="primary", use_container_width=True):
                    if "cart" not in st.session_state:
                        st.session_state.cart = {}
                    st.session_state.cart[pid] = st.session_state.cart.get(pid, 0) + 1
                    st.session_state.wishlist.remove(pid)
                    if user_id:
                        toggle_wishlist(user_id, pid)
                    st.toast(f"Moved {p['name'][:20]} to Cart!")
                    st.rerun()

                if st.button("Remove", key=f"w_del_{pid}", use_container_width=True):
                    st.session_state.wishlist.remove(pid)
                    if user_id:
                        toggle_wishlist(user_id, pid)
                    st.toast("Item removed from wishlist")
                    st.rerun()
