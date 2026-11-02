import streamlit as st
from utils.helpers import money, format_date, get_status_badge, generate_image_svg

def render_return_card(ret: dict):
    """Renders return request card with 7-stage return workflow progress and refund tracking."""
    rid = ret["id"]
    ret_num = ret.get("return_number", f"RET-{rid}")
    order_num = ret.get("order_number", "")
    prod_name = ret.get("product_name", "Product")
    brand = ret.get("brand", "")
    img_url = ret.get("image_url") or "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200"
    status = ret.get("status", "Return Requested")
    reason = ret.get("reason", "")
    comments = ret.get("comments", "")
    created_at = format_date(ret.get("created_at", ""))
    pickup_date = ret.get("pickup_date", "")
    refund_amt = ret.get("refund_amount") or (float(ret.get("unit_price", 0)) * ret.get("quantity", 1))
    refund_status = ret.get("refund_status") or ("Completed" if status == "Refund Completed" else "Processing")
    refund_num = ret.get("refund_number", "")
    tracking_list = ret.get("tracking_list", [])

    with st.container(border=True):
        # Header Row
        c1, c2, c3 = st.columns([3, 1.5, 1.5])
        with c1:
            st.markdown(f"### {ret_num}")
            st.caption(f"Linked to Order: **{order_num}** · Filed on {created_at}")
        with c2:
            st.metric("Refund Amount", money(refund_amt))
        with c3:
            st.markdown("**Return Status**")
            st.markdown(get_status_badge(status, "return"), unsafe_allow_html=True)

        # 7-Stage Return Timeline Stepper
        if status != "Rejected":
            stages = [
                "Return Requested",
                "Under Review",
                "Approved",
                "Pickup Scheduled",
                "Product Received",
                "Refund Initiated",
                "Refund Completed"
            ]
            current_idx = stages.index(status) if status in stages else 0
            st.progress((current_idx + 1) / len(stages))

            # Stepper column labels
            cols = st.columns(len(stages))
            for i, (col, st_name) in enumerate(zip(cols, stages)):
                short_name = st_name.replace("Return ", "").replace("Product ", "").replace("Refund ", "")
                if i < current_idx:
                    col.caption(f"✅ **{short_name}**")
                elif i == current_idx:
                    col.markdown(f'<span style="color:#2563eb; font-weight:700; font-size:0.75rem;">● {short_name}</span>', unsafe_allow_html=True)
                else:
                    col.caption(f"○ {short_name}")
        else:
            st.error("❌ Return Request was Rejected after review.")

        st.divider()

        # Product Info & Details
        p1, p2 = st.columns([1, 4])
        with p1:
            fallback_svg = generate_image_svg("General", prod_name)
            if img_url and (img_url.startswith("http://") or img_url.startswith("https://") or img_url.startswith("data:image/")):
                try:
                    st.image(img_url, width=90)
                except Exception:
                    st.image(fallback_svg, width=90)
            else:
                st.image(fallback_svg, width=90)
        with p2:
            st.markdown(f"**{prod_name}**")
            st.caption(f"Brand: {brand} | Quantity: {ret.get('quantity', 1)} | Reason: **{reason}**")
            if comments:
                st.caption(f"Customer Comments: *\"{comments}\"*")
            if pickup_date:
                st.markdown(f"🚚 **Courier Pickup Scheduled:** `{pickup_date}`")
            if status == "Refund Completed" or refund_status == "Completed":
                st.success(f"💰 Refund of **{money(refund_amt)}** successfully completed ({ret.get('refund_method', 'Original Payment')}). Ref: `{refund_num or 'COMPLETED'}`")

        # Action: View detailed return log
        with st.expander("📋 View Return & Inspection Log", expanded=False):
            if tracking_list:
                for t in tracking_list:
                    st.markdown(f"**{t.get('status')}** — `{t.get('time')}`")
                    st.caption(t.get("note", ""))
                    st.write("---")
            else:
                st.write(f"Return stage: {status}")
