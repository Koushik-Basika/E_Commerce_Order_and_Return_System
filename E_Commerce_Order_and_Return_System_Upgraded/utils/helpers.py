import re
import urllib.parse
from datetime import datetime

def money(amount) -> str:
    """Formats amount into Indian Rupee style string (e.g., ₹4,999 or ₹12,45,800)."""
    try:
        val = float(amount)
        if val.is_integer():
            # Format integer with Indian comma grouping
            orig = f"{int(val)}"
            if len(orig) <= 3:
                return f"₹{orig}"
            last_three = orig[-3:]
            remaining = orig[:-3]
            # Group by 2 for thousands/lakhs/crores
            groups = []
            while remaining:
                groups.insert(0, remaining[-2:])
                remaining = remaining[:-2]
            return f"₹{','.join(groups)},{last_three}"
        else:
            int_part = int(val)
            dec_part = f"{val - int_part:.2f}"[2:]
            orig = str(int_part)
            if len(orig) <= 3:
                return f"₹{orig}.{dec_part}"
            last_three = orig[-3:]
            remaining = orig[:-3]
            groups = []
            while remaining:
                groups.insert(0, remaining[-2:])
                remaining = remaining[:-2]
            return f"₹{','.join(groups)},{last_three}.{dec_part}"
    except (ValueError, TypeError):
        return f"₹{amount}"

def stars(rating: float) -> str:
    """Returns unicode star string for a rating value 1-5."""
    try:
        r = float(rating)
        full = int(round(r))
        full = max(0, min(5, full))
        return "★" * full + "☆" * (5 - full)
    except Exception:
        return "★★★★☆"

def format_date(dt_str: str) -> str:
    """Parses ISO string and returns human-readable format."""
    if not dt_str:
        return ""
    try:
        # Support ISO formats with or without seconds
        clean_str = dt_str.replace("T", " ")
        if "." in clean_str:
            clean_str = clean_str.split(".")[0]
        dt = datetime.fromisoformat(clean_str)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(dt_str)

def get_status_badge(status: str, badge_type: str = "order") -> str:
    """Returns styled HTML badge according to status."""
    st = str(status).strip()
    color_map = {
        # Order statuses
        "Placed": ("#e0f2fe", "#0369a1"),
        "Confirmed": ("#e0e7ff", "#4338ca"),
        "Packed": ("#fef3c7", "#b45309"),
        "Shipped": ("#fde68a", "#92400e"),
        "Out for Delivery": ("#fed7aa", "#c2410c"),
        "Delivered": ("#dcfce7", "#15803d"),
        "Cancelled": ("#fee2e2", "#b91c1c"),

        # Return statuses
        "Return Requested": ("#fef9c3", "#a16207"),
        "Under Review": ("#ffedd5", "#c2410c"),
        "Approved": ("#dbeafe", "#1d4ed8"),
        "Rejected": ("#fee2e2", "#b91c1c"),
        "Pickup Scheduled": ("#ede9fe", "#6d28d9"),
        "Product Received": ("#fae8ff", "#86198f"),
        "Refund Initiated": ("#e0f2fe", "#0284c7"),
        "Refund Completed": ("#dcfce7", "#15803d"),

        # Payment statuses
        "Paid": ("#dcfce7", "#15803d"),
        "Pending": ("#fef3c7", "#b45309"),
        "COD": ("#f1f5f9", "#475569"),
        "Refunded": ("#ccfbf1", "#0f766e"),

        # Stock
        "In Stock": ("#dcfce7", "#15803d"),
        "Low Stock": ("#fef3c7", "#b45309"),
        "Out of Stock": ("#fee2e2", "#b91c1c")
    }

    bg, text = color_map.get(st, ("#f1f5f9", "#475569"))
    return f'<span style="background-color:{bg}; color:{text}; padding:3px 10px; border-radius:12px; font-weight:600; font-size:0.78rem; display:inline-block; border:1px solid rgba(0,0,0,0.06);">{st}</span>'

def generate_image_svg(category: str, title: str) -> str:
    """Generates an elegant data URI SVG placeholder with category branding."""
    cat_colors = {
        "Electronics": ("#3b82f6", "#1d4ed8", "🎧"),
        "Mobiles": ("#06b6d4", "#0e7490", "📱"),
        "Laptops": ("#6366f1", "#4338ca", "💻"),
        "Fashion": ("#ec4899", "#be185d", "👕"),
        "Footwear": ("#f97316", "#c2410c", "👟"),
        "Home & Kitchen": ("#10b981", "#047857", "☕"),
        "Beauty": ("#f43f5e", "#be123c", "✨"),
        "Sports": ("#84cc16", "#4d7c0f", "⚽"),
        "Books": ("#eab308", "#a16207", "📚"),
        "Gaming": ("#8b5cf6", "#6d28d9", "🎮"),
        "Accessories": ("#64748b", "#334155", "🎒")
    }
    c1, c2, icon = cat_colors.get(category, ("#475569", "#1e293b", "🛍️"))
    short_title = (title[:24] + "...") if len(title) > 24 else title
    short_title_clean = re.sub(r"[<>&\"']", "", short_title)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
      <defs>
        <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{c1}"/>
          <stop offset="100%" stop-color="{c2}"/>
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#g)"/>
      <circle cx="200" cy="120" r="45" fill="rgba(255,255,255,0.18)"/>
      <text x="200" y="132" font-size="40" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif">{icon}</text>
      <text x="200" y="195" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif">{short_title_clean}</text>
      <text x="200" y="218" font-size="11" fill="rgba(255,255,255,0.8)" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif">{category.upper()}</text>
    </svg>"""
    encoded = urllib.parse.quote(svg)
    return f"data:image/svg+xml;utf8,{encoded}"
