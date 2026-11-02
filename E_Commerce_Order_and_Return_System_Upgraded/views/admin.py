import json
import streamlit as st
import pandas as pd
import plotly.express as px
from database.repository import (
    get_admin_dashboard_kpis,
    get_admin_sales_chart_data,
    get_admin_category_chart_data,
    get_admin_return_reasons_data,
    get_all_orders_admin,
    update_order_status_admin,
    get_all_returns_admin,
    update_return_status_admin,
    get_all_products_admin,
    add_product_admin,
    update_product_admin,
    delete_product_admin,
    quick_update_stock_admin,
    get_low_stock_products_admin,
    get_all_customers_admin,
    toggle_user_active_admin,
    get_report_data,
    get_categories
)
from utils.helpers import money, format_date, get_status_badge, generate_image_svg

def render_admin_page(user: dict):
    """Renders the comprehensive Admin Console with dashboard, analytics, orders, returns, and reports."""
    st.markdown("""
    <div class="brand-hero" style="background:linear-gradient(135deg, #090d16 0%, #1e1b4b 50%, #312e81 100%);">
        <h1>🛡️ Executive Admin Console</h1>
        <p>E-Commerce Order and Return System Management Portal · Supervise transactions, order fulfillment, return approvals, catalogue inventory, and business intelligence.</p>
    </div>
    """, unsafe_allow_html=True)

    # Admin Navigation Menu
    admin_tab = st.sidebar.radio(
        "Admin Navigation",
        [
            "📊 Dashboard & KPIs",
            "📈 Business Analytics",
            "📦 Order Fulfillment",
            "↩️ Return Desk (Core)",
            "🏷️ Product Management",
            "⚠️ Inventory & Stock Alerts",
            "👥 Customer Directory",
            "📑 Reports & Data Export"
        ]
    )

    # 1. DASHBOARD & KPIS
    if admin_tab == "📊 Dashboard & KPIs":
        st.markdown("### Executive Performance Overview")
        kpis = get_admin_dashboard_kpis()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", money(kpis["total_sales"]))
        c2.metric("Total Orders Placed", f"{kpis['orders_count']:,}")
        c3.metric("Registered Customers", f"{kpis['customers_count']:,}")

        c4, c5, c6 = st.columns(3)
        c4.metric("Active Products in Catalogue", f"{kpis['products_count']:,}")
        c5.metric("Total Return Requests", f"{kpis['returns_count']:,}")
        c6.metric("Completed Refunds Issued", money(kpis["refunds_total"]))

        st.divider()

        # Recent Orders and Recent Returns side by side
        col_ord, col_ret = st.columns(2, gap="medium")
        with col_ord:
            st.markdown("#### 📦 Recent Order Activity")
            recent_orders = get_all_orders_admin()[:6]
            for o in recent_orders:
                with st.container(border=True):
                    st.markdown(f"**{o['order_number']}** · {o['customer_name']}")
                    st.caption(f"{money(o['total'])} · {o['created_at'][:16]}")
                    st.markdown(get_status_badge(o["status"], "order"), unsafe_allow_html=True)

        with col_ret:
            st.markdown("#### ↩️ Recent Return Petitions")
            recent_returns = get_all_returns_admin()[:6]
            for r in recent_returns:
                with st.container(border=True):
                    st.markdown(f"**{r['return_number']}** · {r['product_name'][:25]}")
                    st.caption(f"Reason: {r['reason']} · Customer: {r['customer_name']}")
                    st.markdown(get_status_badge(r["status"], "return"), unsafe_allow_html=True)

    # 2. BUSINESS ANALYTICS
    elif admin_tab == "📈 Business Analytics":
        st.markdown("### Interactive Analytics & Metrics")

        # Sales Trend Chart
        sales_data = get_admin_sales_chart_data()
        if sales_data:
            df_sales = pd.DataFrame(sales_data)
            fig_sales = px.area(
                df_sales,
                x="day",
                y="revenue",
                title="Daily Gross Revenue Trend (₹)",
                labels={"day": "Date", "revenue": "Revenue (₹)"},
                color_discrete_sequence=["#2563eb"]
            )
            fig_sales.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_sales, width="stretch")

        # Category and Return Reason Breakdown
        ch_c1, ch_c2 = st.columns(2)
        with ch_c1:
            cat_data = get_admin_category_chart_data()
            if cat_data:
                df_cat = pd.DataFrame(cat_data)
                fig_cat = px.pie(
                    df_cat,
                    names="category",
                    values="product_count",
                    title="Product Distribution by Category",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_cat.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_cat, width="stretch")

        with ch_c2:
            ret_data = get_admin_return_reasons_data()
            if ret_data:
                df_ret = pd.DataFrame(ret_data)
                fig_ret = px.bar(
                    df_ret,
                    x="reason",
                    y="count",
                    title="Return Requests Breakdown by Reason",
                    labels={"reason": "Customer Return Reason", "count": "Volume"},
                    color="count",
                    color_continuous_scale="Reds"
                )
                fig_ret.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_ret, width="stretch")

    # 3. ORDER FULFILLMENT
    elif admin_tab == "📦 Order Fulfillment":
        st.markdown("### Order Fulfillment & Dispatch Manager")
        oc1, oc2 = st.columns([3, 1.5])
        with oc1:
            ord_search = st.text_input("Search orders by number, customer, or email", placeholder="e.g. ORD-2026-1001")
        with oc2:
            ord_filter = st.selectbox("Status Filter", ["All", "Placed", "Confirmed", "Packed", "Shipped", "Out for Delivery", "Delivered", "Cancelled"])

        orders = get_all_orders_admin(search=ord_search, status=ord_filter)
        st.caption(f"Found {len(orders)} orders")

        for o in orders:
            with st.container(border=True):
                top_1, top_2, top_3 = st.columns([3, 1.5, 1.5])
                with top_1:
                    st.markdown(f"#### {o['order_number']} — {o['customer_name']}")
                    st.caption(f"Email: {o['customer_email']} | Phone: {o.get('customer_phone', 'N/A')}")
                    st.caption(f"Date: {format_date(o['created_at'])} | Address: {o['shipping_address']}")
                with top_2:
                    st.metric("Total", money(o["total"]))
                    st.caption(f"Payment: {o['payment_method']} ({o['payment_status']})")
                with top_3:
                    st.markdown("**Order Stage**")
                    st.markdown(get_status_badge(o["status"], "order"), unsafe_allow_html=True)

                # Items summary
                with st.expander(f"View Order Items ({len(o['items'])})", expanded=False):
                    for it in o["items"]:
                        st.write(f"• {it['product_name']} × {it['quantity']} — {money(it['price'] * it['quantity'])}")

                # Status Transition Control
                st.divider()
                st_c1, st_c2, st_c3 = st.columns([2, 3, 1])
                with st_c1:
                    statuses = ["Placed", "Confirmed", "Packed", "Shipped", "Out for Delivery", "Delivered", "Cancelled"]
                    new_st = st.selectbox(
                        "Update Status",
                        statuses,
                        index=statuses.index(o["status"]) if o["status"] in statuses else 0,
                        key=f"adm_ord_st_{o['id']}"
                    )
                with st_c2:
                    note = st.text_input("Dispatch note / Tracking remark", placeholder="e.g. Dispatched with BlueDart AWB #992182", key=f"adm_ord_note_{o['id']}")
                with st_c3:
                    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                    if st.button("Update", key=f"btn_up_ord_{o['id']}", type="primary"):
                        ok, msg = update_order_status_admin(o["id"], new_st, note)
                        if ok:
                            st.success(msg)
                            st.rerun()

    # 4. RETURN DESK (CORE)
    elif admin_tab == "↩️ Return Desk (Core)":
        st.markdown("### Returns Management & Refund Processing")
        st.caption("Advance return requests through the official 7-stage workflow:")

        rc1, rc2 = st.columns([3, 1.5])
        with rc1:
            ret_search = st.text_input("Search return by return #, order #, or customer", placeholder="e.g. RET-2026-5001")
        with rc2:
            ret_filter = st.selectbox("Stage Filter", [
                "All",
                "Return Requested",
                "Under Review",
                "Approved",
                "Rejected",
                "Pickup Scheduled",
                "Product Received",
                "Refund Initiated",
                "Refund Completed"
            ])

        returns = get_all_returns_admin(search=ret_search, status=ret_filter)
        st.caption(f"Displaying {len(returns)} return petitions")

        for r in returns:
            with st.container(border=True):
                r_c1, r_c2, r_c3 = st.columns([3, 1.5, 1.5])
                with r_c1:
                    st.markdown(f"#### {r['return_number']} · Order {r['order_number']}")
                    st.caption(f"Customer: **{r['customer_name']}** ({r['customer_email']})")
                    st.write(f"Product: **{r['product_name']}** (Qty: {r['quantity']})")
                    st.write(f"Return Reason: **{r['reason']}**")
                    if r.get("comments"):
                        st.caption(f"Customer Comments: *\"{r['comments']}\"*")
                with r_c2:
                    st.metric("Refund Amount", money(r["quantity"] * r.get("item_price", 0)))
                    st.caption(f"Payout Mode: {r.get('refund_method', 'Original Payment')}")
                with r_c3:
                    st.markdown("**Current Stage**")
                    st.markdown(get_status_badge(r["status"], "return"), unsafe_allow_html=True)

                st.divider()

                # 7-Stage Stage Advancement Controls
                all_stages = [
                    "Return Requested",
                    "Under Review",
                    "Approved",
                    "Rejected",
                    "Pickup Scheduled",
                    "Product Received",
                    "Refund Initiated",
                    "Refund Completed"
                ]
                cur_idx = all_stages.index(r["status"]) if r["status"] in all_stages else 0

                ctl_1, ctl_2, ctl_3, ctl_4 = st.columns([2, 2, 2, 1])
                with ctl_1:
                    next_stage = st.selectbox(
                        "Set Stage",
                        all_stages,
                        index=cur_idx,
                        key=f"adm_ret_st_{r['id']}"
                    )
                with ctl_2:
                    pickup_date = None
                    if next_stage == "Pickup Scheduled":
                        pickup_date = st.date_input("Pickup Date", key=f"adm_pk_date_{r['id']}")
                    adm_note = st.text_input("Internal / Customer note", placeholder="Inspection details...", key=f"adm_ret_note_{r['id']}")
                with ctl_3:
                    st.caption("Action details:")
                    if next_stage in ("Refund Initiated", "Refund Completed"):
                        st.caption("💰 Automatically records transaction & credits customer ledger.")
                with ctl_4:
                    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                    if st.button("Apply", key=f"adm_btn_ret_{r['id']}", type="primary"):
                        pk_str = pickup_date.strftime("%Y-%m-%d") if pickup_date else None
                        ok, msg = update_return_status_admin(r["id"], next_stage, adm_note, pk_str)
                        if ok:
                            st.success(msg)
                            st.rerun()

    # 5. PRODUCT MANAGEMENT
    elif admin_tab == "🏷️ Product Management":
        st.markdown("### Catalogue & Product Editor")

        with st.expander("➕ Add New Product to Catalogue", expanded=False):
            with st.form("form_add_prod"):
                an_name = st.text_input("Product Name", placeholder="e.g. Sony WH-1000XM5 Wireless Headphones")
                an_brand = st.text_input("Brand", placeholder="e.g. Sony")
                ac1, ac2 = st.columns(2)
                cats_list = [c["name"] for c in get_categories()]
                an_cat = ac1.selectbox("Category", cats_list)
                an_subcat = ac2.text_input("Subcategory", placeholder="e.g. Wireless Headphones")
                an_desc = st.text_area("Product Description")
                pr1, pr2, pr3 = st.columns(3)
                an_price = pr1.number_input("Selling Price (₹)", min_value=1.0, value=2999.0, step=50.0)
                an_orig_price = pr2.number_input("Original MRP (₹)", min_value=1.0, value=3999.0, step=50.0)
                an_stock = pr3.number_input("Stock Quantity", min_value=0, value=50, step=1)
                an_img = st.text_input("Product Image URL", placeholder="https://images.unsplash.com/...")

                if st.form_submit_button("Add Product to Store", type="primary"):
                    if not an_name.strip() or not an_brand.strip():
                        st.warning("Product name and brand are required.")
                    else:
                        ok, msg = add_product_admin({
                            "name": an_name,
                            "brand": an_brand,
                            "category": an_cat,
                            "subcategory": an_subcat,
                            "description": an_desc,
                            "price": an_price,
                            "original_price": an_orig_price,
                            "stock": an_stock,
                            "image_url": an_img
                        })
                        st.success(msg)
                        st.rerun()

        st.divider()

        # Existing Products Table with Search & Edit
        p_srch = st.text_input("Filter existing products by name, brand, or SKU", placeholder="Search products...")
        prod_page = st.number_input("Page", min_value=1, value=1, step=1)
        prods, total_prods = get_all_products_admin(search=p_srch, page=prod_page, per_page=15)
        st.caption(f"Showing page {prod_page} of {(total_prods + 14)//15} ({total_prods} total products)")

        for p in prods:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 3.5, 2, 1.5])
                with c1:
                    fallback_svg = generate_image_svg(p.get("category", "General"), p["name"])
                    p_img = p.get("image_url", "").strip() if p.get("image_url") else ""
                    if p_img and (p_img.startswith("http://") or p_img.startswith("https://") or p_img.startswith("data:image/")):
                        try:
                            st.image(p_img, width=65)
                        except Exception:
                            st.image(fallback_svg, width=65)
                    else:
                        st.image(fallback_svg, width=65)
                with c2:
                    st.markdown(f"**{p['name']}**")
                    st.caption(f"SKU: `{p['sku']}` | Brand: {p['brand']} | Category: {p['category']}")
                with c3:
                    st.markdown(f"Price: **{money(p['price'])}** (MRP: {money(p['original_price'])})")
                    st.markdown(f"Stock: **{p['stock']}** units")
                with c4:
                    with st.popover("Edit"):
                        with st.form(f"edit_p_{p['id']}"):
                            en_name = st.text_input("Name", value=p["name"])
                            en_brand = st.text_input("Brand", value=p["brand"])
                            en_subcat = st.text_input("Subcategory", value=p["subcategory"])
                            en_price = st.number_input("Price (₹)", value=float(p["price"]))
                            en_orig = st.number_input("Original (₹)", value=float(p["original_price"]))
                            en_stock = st.number_input("Stock", value=int(p["stock"]))
                            en_img = st.text_input("Image URL", value=p.get("image_url") or "")
                            if st.form_submit_button("Save Changes"):
                                update_product_admin(p["id"], {
                                    "name": en_name, "brand": en_brand, "category": p["category"],
                                    "subcategory": en_subcat, "description": p["description"],
                                    "price": en_price, "original_price": en_orig, "stock": en_stock,
                                    "image_url": en_img
                                })
                                st.success("Updated!")
                                st.rerun()

                    if st.button("Delete", key=f"del_p_{p['id']}"):
                        delete_product_admin(p["id"])
                        st.warning("Product removed.")
                        st.rerun()

    # 6. INVENTORY & STOCK ALERTS
    elif admin_tab == "⚠️ Inventory & Stock Alerts":
        st.markdown("### Inventory Health & Low Stock Alerts")
        low_items = get_low_stock_products_admin(threshold=5)

        if low_items:
            st.warning(f"🚨 **Attention Required:** {len(low_items)} product(s) have critical low stock (≤ 5 units).")
            for it in low_items:
                with st.container(border=True):
                    ic1, ic2, ic3 = st.columns([3, 1.5, 1.5])
                    with ic1:
                        st.markdown(f"**{it['name']}**")
                        st.caption(f"SKU: `{it['sku']}` | Brand: {it['brand']}")
                    with ic2:
                        st.markdown(f'<span style="color:#b91c1c; font-weight:700;">⚠ Only {it["stock"]} left!</span>', unsafe_allow_html=True)
                    with ic3:
                        new_stk = st.number_input("Restock amount", min_value=10, value=50, key=f"restk_val_{it['id']}")
                        if st.button("Restock Now", key=f"btn_restk_{it['id']}", type="primary"):
                            quick_update_stock_admin(it["id"], it["stock"] + new_stk)
                            st.success("Stock replenished!")
                            st.rerun()
        else:
            st.success("✓ All inventory levels are healthy across all categories.")

    # 7. CUSTOMER DIRECTORY
    elif admin_tab == "👥 Customer Directory":
        st.markdown("### Customer Directory & Accounts")
        c_srch = st.text_input("Search customers by name, email, or phone", placeholder="Customer lookup...")
        customers = get_all_customers_admin(search=c_srch)

        for cust in customers:
            with st.container(border=True):
                cc1, cc2, cc3 = st.columns([3, 2, 1.5])
                with cc1:
                    st.markdown(f"#### {cust['name']}")
                    st.caption(f"Email: {cust['email']} | Phone: {cust.get('phone', 'N/A')}")
                    st.caption(f"Joined: {format_date(cust['created_at'])}")
                with cc2:
                    st.markdown(f"Orders: **{cust['order_count']}** | Returns: **{cust['return_count']}**")
                    st.markdown(f"Total Lifetime Spend: **{money(cust['total_spent'])}**")
                with cc3:
                    st_label = "Active Account" if cust.get("is_active", 1) else "Deactivated"
                    st.caption(st_label)
                    btn_text = "Deactivate" if cust.get("is_active", 1) else "Activate"
                    if st.button(btn_text, key=f"tgl_u_{cust['id']}"):
                        toggle_user_active_admin(cust["id"])
                        st.rerun()

    # 8. REPORTS & DATA EXPORT
    elif admin_tab == "📑 Reports & Data Export":
        st.markdown("### Exportable Business Reports")
        st.caption("Generate and export full dataset records into CSV format:")

        rep_type = st.selectbox("Select Report to Generate", ["Sales & Orders Report", "Product Catalogue Inventory", "Returns & Refunds Audit", "Customer Account Summary"])

        type_map = {
            "Sales & Orders Report": "sales",
            "Product Catalogue Inventory": "products",
            "Returns & Refunds Audit": "returns",
            "Customer Account Summary": "customers"
        }

        key = type_map[rep_type]
        data = get_report_data(key)

        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, width="stretch")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"📥 Download {rep_type} (CSV)",
                data=csv,
                file_name=f"{key}_report_export.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        else:
            st.info("No data available for this report.")
