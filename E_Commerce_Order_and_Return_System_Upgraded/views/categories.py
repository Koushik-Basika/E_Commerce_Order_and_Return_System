import streamlit as st
from database.repository import get_categories, get_subcategories

def render_categories_page():
    """Renders the categories discovery page with product counts and quick navigation."""
    st.markdown("""
    <div class="section-banner">
        <h2>🏷️ Browse Categories</h2>
        <p>Explore our wide assortment of categories across technology, fashion, lifestyle, and home.</p>
    </div>
    """, unsafe_allow_html=True)

    categories = get_categories()

    # Category Grid (3 columns)
    cols = st.columns(3)
    for i, cat in enumerate(categories):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"""
                <div style="text-align:center; padding:10px 0;">
                    <div style="font-size:2.8rem; margin-bottom:6px;">{cat.get('icon', '🛍️')}</div>
                    <h3 style="margin:0; font-size:1.25rem; font-weight:700; color:#0f172a;">{cat['name']}</h3>
                    <p style="color:#64748b; font-size:0.85rem; margin:6px 0 12px;">{cat.get('description', '')}</p>
                    <span style="background:#e0f2fe; color:#0369a1; padding:3px 12px; border-radius:12px; font-weight:700; font-size:0.8rem;">
                        {cat.get('product_count', 0)} Products
                    </span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
                if st.button(f"Explore {cat['name']}", key=f"cat_browse_{cat['id']}", use_container_width=True, type="primary"):
                    st.session_state.filter_category = cat["name"]
                    st.session_state.nav_page = "shop"
                    st.rerun()

                # Subcategories list
                subcats = get_subcategories(cat["name"])
                if subcats:
                    with st.expander(f"View Subcategories ({len(subcats)})", expanded=False):
                        for sc in subcats:
                            st.write(f"• {sc}")
