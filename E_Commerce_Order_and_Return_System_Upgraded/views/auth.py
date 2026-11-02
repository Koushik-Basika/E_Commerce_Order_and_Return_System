import streamlit as st
from database.repository import authenticate_user, create_user

def render_auth_page():
    """Renders the secure enterprise authentication and account registration interface."""
    st.markdown("""
    <div class="brand-hero">
        <h1>E-Commerce Order and Return System</h1>
        <p>Enterprise shopping platform featuring seamless order fulfillment, automated tracking, and a comprehensive end-to-end return management pipeline.</p>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1.1, 1], gap="large")

    with col_left:
        st.subheader("Enterprise Commerce Platform")
        st.markdown("""
        * **Extensive Catalogue:** Over 750+ verified products across 11 major categories.
        * **Order Lifecycle:** End-to-end fulfillment with visual milestone tracking.
        * **Hassle-Free Returns:** Transparent 7-stage return and refund workflow with warehouse inspection.
        * **Automated Discounts:** Dynamic promotional coupon codes and seasonal campaigns.
        * **Security Architecture:** PBKDF2 HMAC SHA-256 hashed passwords and strict SQL parameterization.
        * **Executive Dashboard:** Real-time analytics, return distribution, and inventory alerts.
        """)

        with st.container(border=True):
            st.markdown("#### 🔒 Security & Data Privacy")
            st.caption("""
            Your personal credentials, address details, and purchase records are isolated and encrypted.
            Role-based authorization guarantees that privileged administrator actions require authenticated administrative access.
            """)

    with col_right:
        with st.container(border=True):
            tab_login, tab_register = st.tabs(["🔐 Sign In", "✨ Create Account"])

            # Login Tab
            with tab_login:
                with st.form("form_login"):
                    st.markdown("### Account Login")
                    email = st.text_input("Email Address", placeholder="user@example.com")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    remember = st.checkbox("Remember this session", value=True)
                    submit_login = st.form_submit_button("Sign In to Account", type="primary", use_container_width=True)

                    if submit_login:
                        if not email or not password:
                            st.warning("Please provide both email and password.")
                        else:
                            user = authenticate_user(email, password)
                            if user:
                                st.session_state.user = user
                                from database.repository import get_user_wishlist_ids
                                st.session_state.wishlist = get_user_wishlist_ids(user["id"])
                                st.session_state.nav_page = "admin" if user.get("role") == "admin" else "home"
                                st.toast(f"Welcome back, {user['name']}!")
                                st.rerun()
                            else:
                                st.error("Invalid email or password. Please verify your credentials and try again.")

            # Registration Tab
            with tab_register:
                with st.form("form_register"):
                    st.markdown("### New Customer Registration")
                    name = st.text_input("Full Name", placeholder="e.g. Rahul Sharma")
                    reg_email = st.text_input("Email Address", placeholder="e.g. rahul@example.com")
                    phone = st.text_input("Phone Number", placeholder="e.g. +91 98450 12345")
                    reg_password = st.text_input("Create Password", type="password", placeholder="Minimum 6 characters")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    address = st.text_area("Default Delivery Address", placeholder="House/Flat No, Street, City, State, PIN Code")

                    submit_reg = st.form_submit_button("Create Account", type="primary", use_container_width=True)

                    if submit_reg:
                        if not name or not reg_email or not reg_password:
                            st.warning("Name, email, and password are required fields.")
                        elif len(reg_password) < 6:
                            st.warning("Password must be at least 6 characters long.")
                        elif reg_password != confirm_password:
                            st.error("Passwords do not match.")
                        else:
                            ok, msg = create_user(name, reg_email, reg_password, phone, address)
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
