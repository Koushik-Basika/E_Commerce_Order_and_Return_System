import streamlit as st
from database.repository import (
    get_user_returns,
    get_user_refunds,
    get_returnable_items_for_user,
    create_return_request
)
from components.return_card import render_return_card
from utils.helpers import money, format_date, get_status_badge

def render_returns_page(user: dict):
    """Renders the dedicated Returns & Refunds dashboard with 7-stage pipeline and refund ledger."""
    st.markdown("""
    <div class="brand-hero" style="background:linear-gradient(135deg, #4c1d95 0%, #6d28d9 50%, #7c3aed 100%);">
        <h1>↩️ Returns & Refunds Center</h1>
        <p>Core feature of E-Commerce Order and Return System. Track your return requests through our 7-stage verification workflow and monitor automated refund credits.</p>
    </div>
    """, unsafe_allow_html=True)

    user_id = user["id"]
    returns_list = get_user_returns(user_id)
    refunds_list = get_user_refunds(user_id)
    returnable_items = get_returnable_items_for_user(user_id)

    # Top KPI Metrics
    total_refunded = sum(float(r["amount"]) for r in refunds_list if r.get("status") == "Completed")
    active_returns_count = len([r for r in returns_list if r["status"] not in ("Refund Completed", "Rejected")])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Return Requests", len(returns_list))
    m2.metric("In Pipeline / In Transit", active_returns_count)
    m3.metric("Completed Refunds", len([r for r in refunds_list if r.get("status") == "Completed"]))
    m4.metric("Total Refunded", money(total_refunded))

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # Sub-tabs
    tab_list, tab_create, tab_refunds = st.tabs([
        "🔄 Return Requests & Tracking",
        "➕ Submit New Return Request",
        "💰 Refund Statements & Ledger"
    ])

    # TAB 1: LIST & TRACKING
    with tab_list:
        st.markdown("### Your Return Requests")
        if not returns_list:
            st.info("You have no active or previous return requests.")
        else:
            for ret in returns_list:
                render_return_card(ret)

    # TAB 2: FILE NEW RETURN
    with tab_create:
        st.markdown("### File a Return for a Delivered Item")
        st.write("Select an eligible item from your delivered orders within our 7-day hassle-free window:")

        if not returnable_items:
            st.warning("No eligible items available for return. Returns can only be requested for orders in 'Delivered' status that have not yet been returned.")
        else:
            with st.container(border=True):
                # Map items for selection
                item_options = {
                    f"{it['order_number']} — {it['product_name']} (Returnable: {it.get('returnable_quantity', it['quantity'])} | {money(it['price'])})": it
                    for it in returnable_items
                }
                selected_label = st.selectbox("Select Delivered Order & Item", list(item_options.keys()))
                chosen_item = item_options[selected_label]
                avail_qty = max(1, int(chosen_item.get("returnable_quantity", chosen_item["quantity"])))

                f_c1, f_c2 = st.columns(2)
                with f_c1:
                    qty = st.number_input("Quantity to Return", min_value=1, max_value=avail_qty, value=1)
                    reason = st.selectbox("Reason for Return", [
                        "Damaged in Transit",
                        "Defective / Not Functioning",
                        "Wrong Product Delivered",
                        "Missing Item / Accessories",
                        "Not as Described on Website",
                        "Size / Dimension Issue",
                        "Quality Not as Expected",
                        "Changed Mind",
                        "Other"
                    ])
                with f_c2:
                    ref_method = st.selectbox("Refund Payout Method", [
                        "Original Payment Method",
                        "UPI (Instant to Registered UPI ID)",
                        "Direct Bank Account Transfer",
                        "Store Credit (Instant)"
                    ])
                    comments = st.text_area("Detailed Explanation & Notes", placeholder="Please describe the defect or reason to assist our warehouse inspection...")

                if st.button("Submit Return Request Now", type="primary", use_container_width=True):
                    ok, msg = create_return_request(
                        order_id=chosen_item["order_id"],
                        order_item_id=chosen_item["id"],
                        product_id=chosen_item["product_id"],
                        user_id=user_id,
                        quantity=qty,
                        reason=reason,
                        comments=comments,
                        refund_method=ref_method
                    )
                    if ok:
                        st.success(msg)
                        st.balloons()
                        st.info("Your request has entered Stage 1: 'Under Review'. Our logistics team will review within 24 hours.")
                        st.rerun()
                    else:
                        st.error(msg)

    # TAB 3: REFUND LEDGER
    with tab_refunds:
        st.markdown("### 💰 Completed and In-Progress Refunds")
        st.caption("All credits processed to your original payment mode or bank account:")

        if not refunds_list:
            st.info("No refunds issued yet.")
        else:
            for ref in refunds_list:
                with st.container(border=True):
                    rc1, rc2, rc3, rc4 = st.columns([2.5, 2, 1.5, 1.5])
                    with rc1:
                        st.markdown(f"**Refund #{ref.get('refund_number', 'REF-000')}**")
                        st.caption(f"Linked Order: {ref.get('order_number', 'N/A')} · {ref.get('product_name')}")
                    with rc2:
                        st.write(f"Txn ID: `{ref.get('transaction_id', 'TXN_REF')}`")
                        st.caption(f"Method: {ref.get('method')}")
                    with rc3:
                        st.markdown(f"**{money(ref['amount'])}**")
                        st.caption(format_date(ref.get("created_at", "")))
                    with rc4:
                        st.markdown(get_status_badge(ref.get("status", "Completed"), "refund"), unsafe_allow_html=True)
