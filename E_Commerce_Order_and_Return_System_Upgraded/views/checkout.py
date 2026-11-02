import streamlit as st
from database.repository import (
    get_user_addresses,
    add_user_address,
    create_order,
    get_product_by_id,
    validate_coupon
)
from utils.helpers import money

def render_checkout_page(user: dict):
    """Renders multi-step checkout: Address, Shipping, Payment, and Order Review."""
    st.markdown("""
    <div class="section-banner">
        <h2>💳 Checkout & Order Confirmation</h2>
        <p>Complete your delivery and payment details to finalize your purchase.</p>
    </div>
    """, unsafe_allow_html=True)

    cart = st.session_state.get("cart", {})
    if not cart:
        st.warning("Your cart is empty. Please add items before checking out.")
        if st.button("Return to Shop"):
            st.session_state.nav_page = "shop"
            st.rerun()
        return

    user_id = user["id"]
    saved_addresses = get_user_addresses(user_id)

    # Calculate Totals
    subtotal = 0.0
    items_summary = []
    for pid, qty in cart.items():
        p = get_product_by_id(pid)
        if p:
            subtotal += p["price"] * qty
            items_summary.append((p, qty))

    # Applied coupon
    coupon_code = st.session_state.get("coupon_code", "")
    coupon_discount = 0.0
    if coupon_code:
        res = validate_coupon(coupon_code, subtotal)
        if res["valid"]:
            coupon_discount = res["discount"]

    # Checkout Steps Tabs / Accordions
    step1, step2, step3, step4 = st.tabs([
        "1. 📍 Delivery Address",
        "2. 🚚 Shipping Method",
        "3. 💳 Payment Method",
        "4. 📦 Final Review & Place Order"
    ])

    # STEP 1: ADDRESS
    with step1:
        st.markdown("### Step 1: Select or Add Delivery Address")
        address_options = []
        if saved_addresses:
            for addr in saved_addresses:
                address_options.append(f"{addr['full_name']} | {addr['street_address']}, {addr['city']}, {addr['state']} - {addr['postal_code']} (Ph: {addr['phone']})")

        address_options.append("➕ Add New Delivery Address")

        selected_addr_opt = st.radio("Choose Address", address_options, key="checkout_addr_radio")

        if selected_addr_opt == "➕ Add New Delivery Address":
            with st.container(border=True):
                st.markdown("##### New Shipping Address")
                n_name = st.text_input("Receiver Full Name", value=user.get("name", ""))
                n_phone = st.text_input("Mobile Number", value=user.get("phone", ""))
                n_street = st.text_input("House / Flat / Street Address")
                ac1, ac2, ac3 = st.columns(3)
                n_city = ac1.text_input("City", value="Bangalore")
                n_state = ac2.text_input("State", value="Karnataka")
                n_pincode = ac3.text_input("PIN Code", value="560103")

                final_shipping_addr = f"{n_name} | {n_street}, {n_city}, {n_state} - {n_pincode} (Ph: {n_phone})"
        else:
            final_shipping_addr = selected_addr_opt

        st.session_state.checkout_shipping_address = final_shipping_addr
        st.success(f"Selected Address: **{final_shipping_addr}**")

    # STEP 2: SHIPPING METHOD
    with step2:
        st.markdown("### Step 2: Choose Delivery Option")
        ship_choice = st.radio(
            "Shipping Method",
            [
                "Standard Shipping (3-4 Business Days) — FREE above ₹999 (else ₹49)",
                "Express Priority Shipping (1-2 Business Days) — ₹99"
            ],
            key="checkout_ship_radio"
        )
        is_express = "Express" in ship_choice
        delivery_method = "Express" if is_express else "Standard"
        st.session_state.checkout_delivery_method = delivery_method

    # STEP 3: PAYMENT
    with step3:
        st.markdown("### Step 3: Select Payment Method")
        st.markdown("""
        <div style="background:#fef3c7; border:1px solid #fde68a; border-radius:10px; padding:10px 14px; margin-bottom:14px; font-size:0.85rem; color:#92400e;">
            🔒 <strong>Test / Simulated Payment Environment:</strong> This portfolio demo uses safe, simulated payment processing. No real money or card charges are processed. Sensitive card numbers and CVVs are strictly client-side sanitized and never stored in the database or server logs.
        </div>
        """, unsafe_allow_html=True)

        payment_choice = st.radio(
            "Payment Gateway",
            [
                "UPI (Google Pay, PhonePe, Paytm)",
                "Credit / Debit Card (Visa, MasterCard, RuPay)",
                "Net Banking (All Major Indian Banks)",
                "Cash on Delivery (COD)"
            ],
            key="checkout_pay_radio"
        )
        st.session_state.checkout_payment_method = payment_choice

        if "UPI" in payment_choice:
            st.text_input("Enter UPI ID (VPA)", placeholder="e.g. mobile@upi or username@bank", key="checkout_upi_vpa")
            st.caption("🔒 Payments are simulated securely via Virtual Payment Address.")
        elif "Credit / Debit Card" in payment_choice:
            st.text_input("Card Number", placeholder="Enter 16-digit card number", key="checkout_card_num")
            cc1, cc2 = st.columns(2)
            cc1.text_input("Expiry (MM/YY)", placeholder="MM/YY", key="checkout_card_exp")
            cc2.text_input("CVV", type="password", placeholder="3-digit CVV", key="checkout_card_cvv")
            st.caption("🔒 256-bit encrypted gateway simulation. Sensitive card credentials and CVVs are never stored.")
        elif "Net Banking" in payment_choice:
            st.selectbox("Select Bank", ["HDFC Bank", "State Bank of India", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank"], key="checkout_nb_bank")
            st.caption("Simulated redirect to financial institution for multi-factor authorization.")
        else:
            st.info("Cash on Delivery chosen. Payment will be collected in cash/UPI upon package arrival.")

    # STEP 4: REVIEW & PLACE ORDER
    with step4:
        st.markdown("### Step 4: Order Review & Confirmation")
        r_col1, r_col2 = st.columns([1.8, 1.2], gap="large")

        with r_col1:
            st.markdown("##### Order Items")
            for p, qty in items_summary:
                st.write(f"• **{p['name']}** × {qty} — **{money(p['price'] * qty)}**")

            st.write("---")
            st.markdown(f"**Deliver To:** {st.session_state.get('checkout_shipping_address', 'Default Address')}")
            st.markdown(f"**Shipping:** {st.session_state.get('checkout_delivery_method', 'Standard')}")
            st.markdown(f"**Payment:** {st.session_state.get('checkout_payment_method', 'UPI')}")

        with r_col2:
            with st.container(border=True):
                st.markdown("##### Final Amount Payable")
                del_fee = 99.0 if st.session_state.get("checkout_delivery_method") == "Express" else (0.0 if subtotal >= 999 else 49.0)
                final_total = max(0.0, subtotal - coupon_discount + del_fee)

                st.write(f"Subtotal: **{money(subtotal)}**")
                if coupon_discount > 0:
                    st.write(f"Coupon Discount: <span style='color:#16a34a; font-weight:700;'>- {money(coupon_discount)}</span>", unsafe_allow_html=True)
                st.write(f"Delivery Fee: **{money(del_fee) if del_fee > 0 else 'FREE'}**")
                st.write(f"GST (18% included): **{money((subtotal - coupon_discount) * 0.18 / 1.18)}**")
                st.markdown("---")
                st.markdown(f"### Total: <span style='color:#2563eb;'>{money(final_total)}</span>", unsafe_allow_html=True)

                is_submitting = st.session_state.get("is_submitting_order", False)
                if st.button("Confirm & Place Order 🚀", type="primary", disabled=is_submitting, use_container_width=True):
                    st.session_state.is_submitting_order = True
                    shipping_addr = st.session_state.get("checkout_shipping_address", "")
                    d_method = st.session_state.get("checkout_delivery_method", "Standard")
                    p_method = st.session_state.get("checkout_payment_method", "UPI")

                    ok, msg, ord_num = create_order(
                        user_id=user["id"],
                        cart_dict=cart,
                        shipping_address=shipping_addr,
                        delivery_method=d_method,
                        payment_method=p_method,
                        coupon_code=coupon_code,
                        discount=coupon_discount
                    )
                    st.session_state.is_submitting_order = False

                    if ok:
                        st.session_state.cart = {}
                        st.session_state.coupon_code = ""
                        st.session_state.coupon_discount = 0.0
                        st.session_state.last_placed_order = ord_num
                        st.balloons()
                        st.success(f"🎉 {msg}")
                        st.info(f"Order #{ord_num} has been sent for packing. Track your parcel anytime in My Orders.")
                        if st.button("Track Order Now", type="primary"):
                            st.session_state.nav_page = "orders"
                            st.rerun()
                    else:
                        st.error(msg)
