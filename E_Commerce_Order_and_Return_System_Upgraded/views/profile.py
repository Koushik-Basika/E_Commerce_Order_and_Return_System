import streamlit as st
from database.repository import (
    get_user_stats,
    update_user_profile,
    get_user_addresses,
    add_user_address
)
from utils.helpers import money

def render_profile_page(user: dict):
    """Renders customer profile, statistics, address book, and account settings."""
    st.markdown("""
    <div class="section-banner">
        <h2>👤 My Account & Profile</h2>
        <p>Manage your personal details, shipping addresses, and review your account activity.</p>
    </div>
    """, unsafe_allow_html=True)

    user_id = user["id"]
    stats = get_user_stats(user_id)

    # Customer Statistics Overview
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Total Orders", stats["orders_count"])
    s2.metric("Total Spending", money(stats["total_spent"]))
    s3.metric("Wishlist Items", stats["wishlist_count"])
    s4.metric("Returns Filed", stats["returns_count"])
    s5.metric("Reviews Shared", stats["reviews_count"])

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    p_col1, p_col2 = st.columns([1.2, 1], gap="large")

    with p_col1:
        with st.container(border=True):
            st.markdown("### Personal Details")
            with st.form("form_edit_profile"):
                name = st.text_input("Full Name", value=user.get("name", ""))
                email = st.text_input("Email Address", value=user.get("email", ""), disabled=True)
                phone = st.text_input("Contact Number", value=user.get("phone", "") or "")
                address = st.text_area("Default Address", value=user.get("address", "") or "")

                if st.form_submit_button("Update Profile Details", type="primary", use_container_width=True):
                    update_user_profile(user_id, name, phone, address)
                    st.session_state.user["name"] = name
                    st.session_state.user["phone"] = phone
                    st.session_state.user["address"] = address
                    st.success("Profile updated successfully!")
                    st.rerun()

    with p_col2:
        with st.container(border=True):
            st.markdown("### Saved Addresses")
            addresses = get_user_addresses(user_id)
            if addresses:
                for a in addresses:
                    def_tag = " <span style='color:#2563eb; font-weight:700;'>(Default)</span>" if a.get("is_default") else ""
                    st.markdown(f"**{a['full_name']}**{def_tag}", unsafe_allow_html=True)
                    st.caption(f"{a['street_address']}, {a['city']}, {a['state']} - {a['postal_code']}")
                    st.caption(f"Phone: {a['phone']}")
                    st.write("---")
            else:
                st.info("No addresses saved yet.")

            with st.popover("➕ Add New Address", use_container_width=True):
                st.markdown("#### Add Shipping Address")
                with st.form("form_new_address"):
                    fn = st.text_input("Full Name", value=user.get("name", ""))
                    ph = st.text_input("Phone Number", value=user.get("phone", ""))
                    strt = st.text_input("Street Address")
                    c1, c2, c3 = st.columns(3)
                    ct = c1.text_input("City", value="Bangalore")
                    stt = c2.text_input("State", value="Karnataka")
                    pin = c3.text_input("PIN Code", value="560103")
                    is_def = st.checkbox("Set as default address", value=True)

                    if st.form_submit_button("Save Address", type="primary"):
                        if not strt.strip() or not ct.strip():
                            st.warning("Please fill in address and city.")
                        else:
                            add_user_address(user_id, fn, ph, strt, ct, stt, pin, int(is_def))
                            st.success("Address added!")
                            st.rerun()
