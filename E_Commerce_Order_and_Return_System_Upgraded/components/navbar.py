import streamlit as st
from database.repository import get_unread_notification_count, get_user_notifications, mark_all_notifications_read

def render_navbar(user: dict = None):
    """Renders the top branding, search bar, notifications, and navigation tabs."""
    cart_count = sum(st.session_state.get("cart", {}).values())
    wish_count = len(st.session_state.get("wishlist", set()))
    user_id = user.get("id") if user else None
    unread_notifs = get_unread_notification_count(user_id) if user_id else 0

    # Top Brand Bar
    top_col1, top_col2, top_col3 = st.columns([4, 1.8, 1.2])

    with top_col1:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <div style="background:#2563eb; color:white; width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; font-weight:800; box-shadow:0 4px 10px rgba(37,99,235,0.3);">🛍️</div>
            <div>
                <span style="font-size:1.35rem; font-weight:800; color:#0f172a; letter-spacing:-0.5px;">E-Commerce Order and Return System</span>
                <span style="display:block; font-size:0.75rem; color:#64748b; font-weight:500;">Complete Catalogue · Smart Orders · Hassle-Free Returns</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with top_col2:
        if user:
            # Notifications Popover
            notif_label = f"🔔 Notifications ({unread_notifs})" if unread_notifs > 0 else "🔔 Notifications"
            with st.popover(notif_label, use_container_width=True):
                st.markdown("### 🔔 In-App Notifications")
                notifs = get_user_notifications(user_id)
                if notifs:
                    if st.button("Mark all as read", key="btn_mark_all_read", use_container_width=True):
                        mark_all_notifications_read(user_id)
                        st.rerun()
                    st.divider()
                    for n in notifs:
                        icon = "📦" if n["type"] == "order" else ("↩️" if n["type"] == "return" else ("🎉" if n["type"] == "deal" else "ℹ️"))
                        unread_dot = "🔴 " if not n["is_read"] else ""
                        st.markdown(f"**{unread_dot}{icon} {n['title']}**")
                        st.caption(n["message"])
                        st.caption(f"_{n['created_at'][:16]}_")
                        st.divider()
                else:
                    st.info("No notifications at this time.")

    with top_col3:
        if user:
            first_name = user.get("name", "User").split()[0]
            with st.popover(f"👤 {first_name}", use_container_width=True):
                st.markdown(f"**{user.get('name')}**")
                st.caption(f"{user.get('email')} · Role: {user.get('role', 'customer').capitalize()}")
                st.divider()
                if st.button("My Profile", key="nav_to_profile_drop", use_container_width=True):
                    st.session_state.nav_page = "profile"
                    st.rerun()
                if user.get("role") == "admin":
                    if st.button("Admin Dashboard", key="nav_to_admin_drop", use_container_width=True):
                        st.session_state.nav_page = "admin"
                        st.rerun()
                if st.button("Sign Out", key="nav_logout_btn", type="primary", use_container_width=True):
                    st.session_state.user = None
                    st.session_state.cart = {}
                    st.session_state.wishlist = set()
                    st.session_state.nav_page = "home"
                    st.rerun()

    # Universal Search Bar in Navigation Header (clearly visible across all pages)
    current_search = st.session_state.get("search_query", "")

    if current_search:
        s_col_input, s_col_btn, s_col_clear = st.columns([5.5, 1.2, 1.0])
        with s_col_clear:
            if st.button("✕ Clear", key="nav_clear_search_btn"):
                st.session_state.search_query = ""
                st.session_state.order_search_query = ""
                st.session_state.shop_page_num = 1
                st.rerun()
    else:
        s_col_input, s_col_btn = st.columns([5.8, 1.2])

    with s_col_input:
        navbar_q = st.text_input(
            "Search products, categories, brands, or orders...",
            value=current_search,
            placeholder="🔍 Search products, categories, brands, SKUs, or order numbers...",
            label_visibility="collapsed",
            key="navbar_global_search_input"
        )

    with s_col_btn:
        search_submitted = st.button("Search", key="nav_search_submit_btn", type="primary")

    # Handle Search Submission (Enter key or button click)
    if (search_submitted or (navbar_q != current_search and navbar_q.strip())) and (navbar_q.strip() or current_search):
        q_clean = navbar_q.strip()
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

    st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)

    # Navigation Bar Buttons
    current_page = st.session_state.get("nav_page", "home")

    nav_cols = st.columns([1, 1, 1.1, 1.2, 1.1, 1.1, 1.1, 1.4, 1.1])

    # 1. Home
    with nav_cols[0]:
        if st.button("🏠 Home", use_container_width=True, type="primary" if current_page == "home" else "secondary"):
            st.session_state.nav_page = "home"
            st.rerun()

    # 2. Products / Shop
    with nav_cols[1]:
        if st.button("🛍️ Shop", use_container_width=True, type="primary" if current_page == "shop" else "secondary"):
            st.session_state.nav_page = "shop"
            st.rerun()

    # 3. Categories
    with nav_cols[2]:
        if st.button("🏷️ Categories", use_container_width=True, type="primary" if current_page == "categories" else "secondary"):
            st.session_state.nav_page = "categories"
            st.rerun()

    # 4. Deals & Offers
    with nav_cols[3]:
        if st.button("⚡ Deals & Offers", use_container_width=True, type="primary" if current_page == "deals" else "secondary"):
            st.session_state.nav_page = "deals"
            st.rerun()

    # 5. Wishlist
    with nav_cols[4]:
        w_text = f"❤️ Wishlist ({wish_count})" if wish_count > 0 else "❤️ Wishlist"
        if st.button(w_text, use_container_width=True, type="primary" if current_page == "wishlist" else "secondary"):
            st.session_state.nav_page = "wishlist"
            st.rerun()

    # 6. Cart
    with nav_cols[5]:
        c_text = f"🛒 Cart ({cart_count})" if cart_count > 0 else "🛒 Cart"
        if st.button(c_text, use_container_width=True, type="primary" if current_page == "cart" else "secondary"):
            st.session_state.nav_page = "cart"
            st.rerun()

    # 7. Orders
    with nav_cols[6]:
        if st.button("📦 Orders", use_container_width=True, type="primary" if current_page == "orders" else "secondary"):
            st.session_state.nav_page = "orders"
            st.rerun()

    # 8. Returns & Refunds (Core)
    with nav_cols[7]:
        if st.button("↩️ Returns & Refunds", use_container_width=True, type="primary" if current_page == "returns" else "secondary"):
            st.session_state.nav_page = "returns"
            st.rerun()

    # 9. Admin or Profile
    with nav_cols[8]:
        if user and user.get("role") == "admin":
            if st.button("🛡️ Admin", use_container_width=True, type="primary" if current_page == "admin" else "secondary"):
                st.session_state.nav_page = "admin"
                st.rerun()
        else:
            if st.button("👤 Profile", use_container_width=True, type="primary" if current_page == "profile" else "secondary"):
                st.session_state.nav_page = "profile"
                st.rerun()

    st.markdown("<div style='margin-bottom:1.2rem;'></div>", unsafe_allow_html=True)
