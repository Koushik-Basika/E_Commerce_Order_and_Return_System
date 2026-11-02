def get_custom_css():
    """Returns custom CSS for E-Commerce Order and Return System."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        background-color: #f8fafc;
        color: #0f172a;
    }

    /* Top padding fix */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 4rem !important;
        max-width: 1440px !important;
    }

    /* Brand Header & Hero */
    .brand-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #2563eb 100%);
        border-radius: 20px;
        padding: 2.8rem 3rem;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.2);
        position: relative;
        overflow: hidden;
    }
    .brand-hero::after {
        content: "";
        position: absolute;
        top: -40%;
        right: -10%;
        width: 380px;
        height: 380px;
        background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0) 70%);
        border-radius: 50%;
    }
    .brand-hero h1 {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin: 0;
        color: #ffffff;
    }
    .brand-hero p {
        font-size: 1.1rem;
        color: #e2e8f0;
        margin: 0.6rem 0 0 0;
        font-weight: 400;
        max-width: 650px;
        line-height: 1.5;
    }

    /* Sub-banners */
    .section-banner {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    }
    .section-banner h2 {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        color: #0f172a;
    }
    .section-banner p {
        color: #64748b;
        margin: 0.25rem 0 0 0;
        font-size: 0.92rem;
    }

    /* Modern Product Card */
    .product-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        height: 100%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        margin-bottom: 1rem;
    }
    .product-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px -6px rgba(15, 23, 42, 0.1);
        border-color: #cbd5e1;
    }
    .product-box img {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 12px;
        background-color: #f1f5f9;
        margin-bottom: 10px;
    }
    .prod-brand {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #2563eb;
        margin-bottom: 4px;
    }
    .prod-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #0f172a;
        line-height: 1.35;
        height: 2.7em;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        margin-bottom: 6px;
    }
    .prod-rating {
        font-size: 0.8rem;
        color: #f59e0b;
        display: flex;
        align-items: center;
        gap: 4px;
        margin-bottom: 8px;
    }
    .prod-rating span {
        color: #64748b;
        font-size: 0.75rem;
    }
    .prod-price-row {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-top: 4px;
        margin-bottom: 10px;
    }
    .prod-price {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0f172a;
    }
    .prod-orig-price {
        font-size: 0.85rem;
        color: #94a3b8;
        text-decoration: line-through;
    }
    .prod-discount {
        font-size: 0.78rem;
        font-weight: 700;
        color: #16a34a;
        background: #dcfce7;
        padding: 2px 6px;
        border-radius: 6px;
    }

    /* Badges */
    .badge-stock {
        font-size: 0.75rem;
        font-weight: 600;
        color: #16a34a;
        margin-bottom: 8px;
    }
    .badge-low-stock {
        font-size: 0.75rem;
        font-weight: 600;
        color: #b45309;
        margin-bottom: 8px;
    }

    /* Metrics and Admin Cards */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 1.2rem;
        border-radius: 16px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    }
    div[data-testid="stMetric"] label {
        color: #64748b !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 800 !important;
    }

    /* Timeline Stepper */
    .stepper-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 1.5rem 0;
        position: relative;
    }
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        z-index: 1;
        flex: 1;
    }
    .step-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.82rem;
        font-weight: 700;
        margin-bottom: 6px;
        border: 2px solid #e2e8f0;
        background: white;
        color: #94a3b8;
    }
    .step-circle.active {
        background: #2563eb;
        color: white;
        border-color: #2563eb;
        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15);
    }
    .step-circle.completed {
        background: #16a34a;
        color: white;
        border-color: #16a34a;
    }
    .step-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #475569;
        text-align: center;
    }

    /* Category Cards */
    .cat-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem 1rem;
        text-align: center;
        transition: all 0.2s ease;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
    }
    .cat-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px -5px rgba(15, 23, 42, 0.08);
        border-color: #2563eb;
    }
    .cat-icon {
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }
    .cat-name {
        font-weight: 700;
        font-size: 1.05rem;
        color: #0f172a;
    }
    .cat-count {
        color: #64748b;
        font-size: 0.82rem;
        margin-top: 4px;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        transition: all 0.15s ease !important;
    }
    .stButton>button[kind="primary"] {
        background: #2563eb !important;
        border-color: #2563eb !important;
    }
    .stButton>button[kind="primary"]:hover {
        background: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }

    /* Footer */
    .app-footer {
        border-top: 1px solid #e2e8f0;
        margin-top: 3.5rem;
        padding-top: 2rem;
        text-align: center;
        color: #64748b;
        font-size: 0.85rem;
        line-height: 1.6;
    }
    .app-footer strong {
        color: #1e3a8a;
    }
    </style>
    """
