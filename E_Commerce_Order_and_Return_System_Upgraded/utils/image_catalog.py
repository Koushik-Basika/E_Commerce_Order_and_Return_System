"""
E-Commerce Order and Return System — Image Catalog Manager
Loads, indexes, and deterministically maps 300+ unique verified product images
from data/product_images.json across categories and subcategories.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional
from utils.helpers import generate_image_svg

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(BASE_DIR, "data", "product_images.json")

_CATALOG_CACHE: Optional[List[Dict]] = None
_CATEGORY_INDEX: Optional[Dict[str, List[Dict]]] = None
_SUBCATEGORY_INDEX: Optional[Dict[str, List[Dict]]] = None
_ID_INDEX: Optional[Dict[str, Dict]] = None

def load_image_catalog(force_reload: bool = False) -> List[Dict]:
    """Loads and caches data/product_images.json asset manifest."""
    global _CATALOG_CACHE, _CATEGORY_INDEX, _SUBCATEGORY_INDEX, _ID_INDEX

    if _CATALOG_CACHE is not None and not force_reload:
        return _CATALOG_CACHE

    if not os.path.exists(CATALOG_PATH):
        raise FileNotFoundError(f"Image catalog manifest not found at: {CATALOG_PATH}")

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Index by category and subcategory
    cat_idx: Dict[str, List[Dict]] = {}
    subcat_idx: Dict[str, List[Dict]] = {}
    id_idx: Dict[str, Dict] = {}

    for item in catalog:
        cat = item.get("category", "General")
        subcat = item.get("subcategory", "General")
        img_id = item.get("id", "")

        cat_idx.setdefault(cat, []).append(item)
        subcat_key = f"{cat}::{subcat}"
        subcat_idx.setdefault(subcat_key, []).append(item)
        if img_id:
            id_idx[img_id] = item

    _CATALOG_CACHE = catalog
    _CATEGORY_INDEX = cat_idx
    _SUBCATEGORY_INDEX = subcat_idx
    _ID_INDEX = id_idx

    return _CATALOG_CACHE

def get_catalog_stats() -> Dict:
    """Returns catalog summary statistics including unique URL count and category breakdowns."""
    catalog = load_image_catalog()
    urls = {item["url"] for item in catalog}
    cat_counts = {}
    for item in catalog:
        c = item.get("category", "General")
        cat_counts[c] = cat_counts.get(c, 0) + 1

    return {
        "total_entries": len(catalog),
        "unique_urls": len(urls),
        "category_counts": cat_counts
    }

def get_images_for_category(category: str) -> List[Dict]:
    """Returns list of image entries matching category."""
    load_image_catalog()
    assert _CATEGORY_INDEX is not None
    if category in _CATEGORY_INDEX:
        return _CATEGORY_INDEX[category]
    # Fallback to general or first available
    return _CATALOG_CACHE or []

def get_images_for_subcategory(category: str, subcategory: str) -> List[Dict]:
    """Returns list of image entries matching category and subcategory, supplemented to ensure rich diversity."""
    load_image_catalog()
    assert _SUBCATEGORY_INDEX is not None
    key = f"{category}::{subcategory}"
    subcat_imgs = _SUBCATEGORY_INDEX.get(key, [])
    cat_imgs = get_images_for_category(category)
    if len(subcat_imgs) >= 24:
        return subcat_imgs
    
    combined = list(subcat_imgs)
    seen_urls = {item["url"] for item in combined}
    for item in cat_imgs:
        if item["url"] not in seen_urls:
            combined.append(item)
            seen_urls.add(item["url"])
    return combined if combined else cat_imgs

def get_deterministic_product_image(
    category: str,
    subcategory: str = "",
    product_identifier: str = "",
    offset: int = 0
) -> str:
    """
    Deterministically maps a product (via category, subcategory, SKU or identifier)
    to a unique verified image URL. Ensures stability across Streamlit reruns.
    """
    pool = get_images_for_subcategory(category, subcategory) if subcategory else get_images_for_category(category)
    if not pool:
        pool = get_images_for_category(category)
    if not pool:
        return generate_image_svg(category, product_identifier or "Product")

    # Stable hash index
    seed_str = f"{category}:{subcategory}:{product_identifier}:{offset}"
    hash_val = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
    idx = hash_val % len(pool)
    return pool[idx]["url"]

def get_product_gallery_images(
    category: str,
    subcategory: str = "",
    primary_url: str = "",
    product_identifier: str = "",
    count: int = 3
) -> List[str]:
    """
    Returns gallery/variant image URLs for a product.
    Tries entry's gallery_urls first, then distinct items from the subcategory pool.
    """
    load_image_catalog()
    gallery: List[str] = []

    # Check if primary image has gallery angles defined
    if primary_url and _CATALOG_CACHE:
        for it in _CATALOG_CACHE:
            if it.get("url") == primary_url and it.get("gallery_urls"):
                for g in it["gallery_urls"]:
                    if g not in gallery and g != primary_url:
                        gallery.append(g)
            if len(gallery) >= count:
                break

    # If need more angles, pick alternate verified images from the category pool
    if len(gallery) < count:
        pool = get_images_for_subcategory(category, subcategory)
        if len(pool) < count:
            pool = get_images_for_category(category)
        
        # Pick adjacent deterministic candidates
        for i in range(1, count + 3):
            cand = get_deterministic_product_image(category, subcategory, product_identifier, offset=i)
            if cand != primary_url and cand not in gallery:
                gallery.append(cand)
            if len(gallery) >= count:
                break

    # Fallback to primary if empty
    if not gallery and primary_url:
        gallery = [primary_url]

    return gallery[:count]
