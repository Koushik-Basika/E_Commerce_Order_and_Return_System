
import streamlit as st
from utils.helpers import money, format_date, get_status_badge, generate_image_svg
from utils.invoice import generate_invoice_html

def render_order_card(order: dict, user: dict, on_cancel=None, on_return=None):
    """Renders a comprehensive order card with visual tracking timeline and order actions."""
    oid = order["id"]
    order_num = order.get("order_number", f"ORD-{oid}")
    created_at = format_date(order.get("created_at", ""))
    total = order.get("total", 0.0)
    status = order.get("status", "Placed")
    items = order.get("items", [])
    expected_del = order.get("expected_delivery", "")
    address = order.get("shipping_address") or order.get("address", "")
    tracking_list = order.get("tracking_list", [])

    with st.container(border=True):
        # Header Row
        c1, c2, c3, c4 = st.columns([2.5, 1.5, 1.5, 1.5])
        with c1:
            st.markdown(f"### {order_num}")
            st.caption(f"Placed on {created_at} · Payment: {order.get('payment_method', 'Online')}")
        with c2:
            st.metric("Total Amount", money(total))
        with c3:
            st.markdown("**Order Status**")
            st.markdown(get_status_badge(status, "order"), unsafe_allow_html=True)
        with c4:
            st.markdown("**Delivery Date**")
            st.caption(expected_del or "Estimated 2-4 days")

        # Visual Stepper Timeline (if not Cancelled)
        if status != "Cancelled":
            steps = ["Placed", "Confirmed", "Packed", "Shipped", "Out for Delivery", "Delivered"]
            current_idx = steps.index(status) if status in steps else 0
            pct = (current_idx + 1) / len(steps)
            st.progress(pct)

            # Stepper text
            cols = st.columns(len(steps))
            for i, (col, step_name) in enumerate(zip(cols, steps)):
                if i < current_idx:
                    col.caption(f"✅ **{step_name}**")
                elif i == current_idx:
                    col.markdown(f'<span style="color:#2563eb; font-weight:700; font-size:0.8rem;">● {step_name}</span>', unsafe_allow_html=True)
                else:
                    col.caption(f"○ {step_name}")
        else:
            st.error("❌ This order was cancelled.")

        st.divider()

        # Item Rows
        st.markdown("**Ordered Items**")
        for item in items:
            ic1, ic2, ic3, ic4 = st.columns([1, 4, 1.5, 1.5])
            with ic1:
                item_name = item.get("product_name") or item.get("name", "Product")
                fallback_svg = generate_image_svg("General", item_name)
                img = item.get("image_url", "").strip() if item.get("image_url") else ""
                if img and (img.startswith("http://") or img.startswith("https://") or img.startswith("data:image/")):
                    try:
                        st.image(img, width=65)
                    except Exception:
                        st.image(fallback_svg, width=65)
                else:
                    st.image(fallback_svg, width=65)
            with ic2:
                st.markdown(f"**{item.get('product_name') or item.get('name')}**")
                st.caption(f"Brand: {item.get('brand', 'Standard')} | Unit: {money(item['price'])}")
            with ic3:
                st.write(f"Qty: **{item['quantity']}**")
            with ic4:
                st.markdown(f"**{money(item['price'] * item['quantity'])}**")
                if item.get("has_return"):
                    st.caption("↩️ Return Filed")

        st.caption(f"📍 Shipping Address: {address}")

        st.divider()

        # Actions Bar
        a1, a2, a3, a4 = st.columns(4)

        # 1. Tracking History Modal/Expander
        with a1:
            with st.popover("📍 Track Order", use_container_width=True):
                st.markdown(f"#### Tracking History — {order_num}")
                if tracking_list:
                    for t in tracking_list:
                        st.markdown(f"**{t.get('status')}** · `{t.get('time')}`")
                        st.caption(t.get("note", ""))
                        st.write("---")
                else:
                    st.info(f"Current stage: {status}")

        # 2. Invoice View/Download
        with a2:
            with st.popover("🧾 View Invoice", use_container_width=True):
                st.markdown(f"#### Tax Invoice — {order_num}")
                inv_html = generate_invoice_html(order, items, user)
                st.components.v1.html(inv_html, height=500, scrolling=True)
                st.download_button(
                    label="Download HTML Invoice",
                    data=inv_html,
                    file_name=f"Invoice_{order_num}.html",
                    mime="text/html",
                    key=f"dl_inv_{oid}",
                    use_container_width=True
                )

        # 3. Cancel Order (if Placed or Confirmed)
        with a3:
            if status in ("Placed", "Confirmed"):
                with st.popover("❌ Cancel Order", use_container_width=True):
                    st.write("Are you sure you want to cancel this order?")
                    cancel_reason = st.selectbox("Reason for cancellation", [
                        "Changed mind", "Found better price elsewhere", "Delivery time too long", "Ordered by mistake", "Other"
                    ], key=f"c_rs_{oid}")
                    if st.button("Confirm Cancellation", type="primary", key=f"btn_cancel_{oid}", use_container_width=True):
                        if on_cancel:
                            on_cancel(oid, cancel_reason)

        # 4. Return Product (if Delivered and eligible)
        with a4:
            if status == "Delivered":
                eligible_items = [it for it in items if (it.get("quantity", 1) - it.get("returned_quantity", 0)) > 0]
                if eligible_items:
                    with st.popover("↩️ Return Item", use_container_width=True):
                        st.markdown("#### File Return Request")
                        st.write("Choose the item you want to return:")
                        item_map = {f"{it['product_name']} (Eligible Qty: {it['quantity'] - it.get('returned_quantity', 0)})": it for it in eligible_items}
                        sel_label = st.selectbox("Select Item", list(item_map.keys()), key=f"ret_it_sel_{oid}")
                        sel_item = item_map[sel_label]
                        rem_qty = max(1, sel_item["quantity"] - sel_item.get("returned_quantity", 0))

                        qty_ret = st.number_input("Quantity to return", min_value=1, max_value=rem_qty, value=1, key=f"ret_qty_{oid}")
                        reason = st.selectbox("Return Reason", [
                            "Damaged", "Defective", "Wrong Product", "Missing Item",
                            "Not as Described", "Size Issue", "Quality Issue", "Changed Mind", "Other"
                        ], key=f"ret_rs_{oid}")
                        comments = st.text_area("Additional comments / details", placeholder="Provide details to assist inspection...", key=f"ret_cm_{oid}")
                        ref_method = st.selectbox("Refund Preference", ["Original Payment", "UPI (Google Pay / PhonePe)", "Direct Bank Transfer"], key=f"ret_pm_{oid}")

                        if st.button("Submit Return Request", type="primary", key=f"ret_sub_{oid}", use_container_width=True):
                            if on_return:
                                on_return(oid, sel_item["id"], sel_item["product_id"], qty_ret, reason, comments, ref_method)
                else:
                    st.caption("All items returned")
