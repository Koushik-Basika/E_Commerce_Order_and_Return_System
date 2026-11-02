import streamlit as st
from database.repository import get_user_orders, cancel_order, create_return_request
from components.order_card import render_order_card

def render_orders_page(user: dict):
    """Renders customer orders list with visual timeline, tracking, cancellation, and returns."""
    st.markdown("""
    <div class="section-banner">
        <h2>📦 My Orders & Tracking</h2>
        <p>Monitor your active order lifecycle stages, download tax invoices, and initiate product returns.</p>
    </div>
    """, unsafe_allow_html=True)

    user_id = user["id"]

    # Order Search Bar
    prefill_order_search = st.session_state.get("order_search_query", "")

    if prefill_order_search:
        o_col1, o_col_clear = st.columns([5, 1.2])
        with o_col_clear:
            if st.button("✕ Clear Search", key="btn_clear_order_search", use_container_width=True):
                st.session_state.order_search_query = ""
                st.rerun()
    else:
        o_col1 = st.container()

    with o_col1:
        ord_input = st.text_input(
            "Search Orders",
            value=prefill_order_search,
            placeholder="🔍 Search your orders by Order # (e.g. ORD-20261013-1234) or shipping address...",
            label_visibility="collapsed",
            key="orders_search_input_val"
        )
        if ord_input != prefill_order_search:
            st.session_state.order_search_query = ord_input.strip()
            st.rerun()

    active_order_search = st.session_state.get("order_search_query", "")

    # Filter tabs
    status_tabs = ["All Orders", "Active / In Transit", "Delivered", "Cancelled"]
    sel_tab = st.radio("Filter Orders", status_tabs, horizontal=True, label_visibility="collapsed")

    status_filter = "All"
    if sel_tab == "Active / In Transit":
        status_filter = "Active"
    elif sel_tab == "Delivered":
        status_filter = "Delivered"
    elif sel_tab == "Cancelled":
        status_filter = "Cancelled"

    orders = get_user_orders(user_id, status_filter=status_filter, search=active_order_search)

    if not orders:
        st.info("No orders found matching the selected filter.")
        if st.button("Start Shopping"):
            st.session_state.nav_page = "shop"
            st.rerun()
        return

    st.caption(f"Displaying {len(orders)} orders")

    # Cancel Callback
    def handle_cancel(order_id, reason):
        ok, msg = cancel_order(order_id, user_id, reason)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    # Return Callback
    def handle_return(order_id, order_item_id, product_id, qty, reason, comments, ref_method):
        ok, msg = create_return_request(order_id, order_item_id, product_id, user_id, qty, reason, comments, ref_method)
        if ok:
            st.success(msg)
            st.info("Your return has been filed. Track progress under the 'Returns & Refunds' tab.")
            st.rerun()
        else:
            st.error(msg)

    # Render each order card
    for o in orders:
        render_order_card(o, user, on_cancel=handle_cancel, on_return=handle_return)
