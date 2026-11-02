"""
E-Commerce Order and Return System — Scalable Product Catalogue Generator & Batch Importer
Supports scaling the product catalogue to 1,000,000+ unique records with:
- Deterministic, collision-free unique SKU generation
- Realistic, category-appropriate specifications and attributes
- High-throughput streaming batch insertion (executemany in chunks)
- Data integrity verification & duplicate detection
"""

import sys
import os
import json
import time
import random
import sqlite3
from datetime import datetime

# Add root directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.connection import get_connection
from utils.image_catalog import get_deterministic_product_image, get_product_gallery_images

CATEGORY_TAXONOMY = {
    "Electronics": {
        "code": "ELE",
        "brands": ["Sony", "Bose", "Sennheiser", "JBL", "Boat", "Audio-Technica", "Marshall", "Anker"],
        "subcategories": ["Wireless Headphones", "Bluetooth Speakers", "Soundbars", "Earbuds", "Studio Monitors"],
        "price_range": (999, 39999),
        "spec_templates": [
            {"connectivity": "Bluetooth 5.3", "battery_life": "30 Hours", "noise_cancellation": "Active ANC", "driver_size": "40mm"},
            {"connectivity": "Bluetooth 5.2", "water_resistance": "IPX7", "output_power": "40W RMS", "battery_life": "16 Hours"},
            {"connectivity": "Lossless 2.4GHz + BT", "frequency_response": "10Hz - 40kHz", "weight": "250g"}
        ],
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80"
    },
    "Mobiles": {
        "code": "MOB",
        "brands": ["Samsung", "Apple", "OnePlus", "Xiaomi", "Google", "Realme", "Motorola", "iQOO"],
        "subcategories": ["5G Smartphones", "Flagship Phones", "Budget Phones", "Foldable Phones"],
        "price_range": (8999, 149999),
        "spec_templates": [
            {"ram": "8GB / 12GB LPDDR5X", "storage": "256GB UFS 4.0", "display": "6.7\" 120Hz AMOLED", "battery": "5000mAh 80W"},
            {"ram": "6GB LPDDR4X", "storage": "128GB UFS 3.1", "display": "6.5\" 90Hz FHD+", "battery": "5000mAh 33W"},
            {"ram": "16GB LPDDR5X", "storage": "512GB UFS 4.0", "display": "6.82\" 2K LTPO AMOLED", "battery": "5400mAh 100W"}
        ],
        "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80"
    },
    "Laptops": {
        "code": "LAP",
        "brands": ["Dell", "HP", "Lenovo", "Apple", "Asus", "Acer", "MSI"],
        "subcategories": ["Ultrabooks", "Gaming Laptops", "Business Laptops", "2-in-1 Touch Laptops"],
        "price_range": (32999, 249999),
        "spec_templates": [
            {"processor": "Intel Core i7 14th Gen", "ram": "16GB DDR5", "storage": "1TB NVMe SSD", "display": "15.6\" OLED 120Hz"},
            {"processor": "AMD Ryzen 7 8845HS", "graphics": "RTX 4060 8GB", "ram": "16GB DDR5", "storage": "1TB SSD", "display": "16\" 165Hz QHD"},
            {"processor": "Apple M3 Pro Chip", "unified_memory": "18GB", "storage": "512GB SSD", "display": "14.2\" Liquid Retina XDR"}
        ],
        "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80"
    },
    "Fashion": {
        "code": "FAS",
        "brands": ["Levi's", "Zara", "Tommy Hilfiger", "Van Heusen", "Allen Solly", "US Polo", "H&M"],
        "subcategories": ["Slim Fit Shirts", "Denim Jeans", "Jackets & Blazers", "Cotton Polos", "Ethnic Wear"],
        "price_range": (699, 12999),
        "spec_templates": [
            {"material": "100% Giza Cotton", "fit": "Slim Fit", "weave": "Oxford Twill", "care": "Machine Wash Warm"},
            {"material": "Stretch Denim (98% Cotton, 2% Elastane)", "rise": "Mid Rise", "fit": "Tapered Slim", "care": "Cold Wash"},
            {"material": "Poly-Viscose Blend", "lining": "100% Satin Polyester", "closure": "Two Button Single Breasted"}
        ],
        "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&q=80"
    },
    "Footwear": {
        "code": "FTW",
        "brands": ["Nike", "Adidas", "Puma", "Reebok", "Asics", "New Balance", "Clarks", "Skechers"],
        "subcategories": ["Running Shoes", "Lifestyle Sneakers", "Training Shoes", "Formal Leather Shoes"],
        "price_range": (1499, 21999),
        "spec_templates": [
            {"upper": "Engineered Breathable Mesh", "cushioning": "Zoom Air / Boost Foam", "outsole": "Continental Rubber", "weight": "260g"},
            {"upper": "Full Grain Genuine Leather", "sole": "Vibram High-Traction", "closure": "Lace-Up", "heel": "Stack Leather"},
            {"upper": "Knit Fabric", "midsole": "EVA Responsive Foam", "terrain": "Road & Track"}
        ],
        "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80"
    },
    "Home & Kitchen": {
        "code": "HMK",
        "brands": ["Philips", "Prestige", "Bajaj", "Morphy Richards", "Havells", "Bosch", "Milton"],
        "subcategories": ["Air Fryers", "Coffee Makers", "Mixer Grinders", "Induction Cooktops", "Cookware Sets"],
        "price_range": (999, 34999),
        "spec_templates": [
            {"capacity": "4.2 Litres", "power": "1400 Watts", "technology": "Rapid Air 360", "warranty": "2 Years"},
            {"capacity": "1.5 Litre Carafe", "pressure": "15 Bar Italian Pump", "grinder": "Conical Burr", "power": "1350W"},
            {"motor": "750 Watt Heavy Duty Copper", "jars": "3 Stainless Steel Jars + 1 Juicer", "speed": "3 Speeds + Pulse"}
        ],
        "image": "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=800&q=80"
    },
    "Beauty": {
        "code": "BTY",
        "brands": ["L'Oreal", "Minimalist", "The Ordinary", "Forest Essentials", "Neutrogena", "Cetaphil", "Biotique"],
        "subcategories": ["Face Serums", "Sunscreen & SPF", "Moisturizers", "Hair Cleansers", "Fragrances"],
        "price_range": (349, 5999),
        "spec_templates": [
            {"volume": "30ml", "key_actives": "10% Niacinamide + 1% Zinc PCA", "skin_type": "All Skin Types / Acne Prone", "dermatologist_tested": "Yes"},
            {"volume": "50g", "spf": "SPF 50+ PA++++", "filter_type": "Hybrid Broad Spectrum", "finish": "Matte Invisible"},
            {"volume": "100ml", "fragrance_family": "Woody Oriental", "top_notes": "Bergamot, Cardamom", "concentration": "Eau de Parfum"}
        ],
        "image": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800&q=80"
    },
    "Sports": {
        "code": "SPT",
        "brands": ["Decathlon", "Yonex", "Cosco", "Nivia", "Kiprun", "Domyos", "SG Cricket"],
        "subcategories": ["Badminton Rackets", "Fitness Equipment", "Football & Soccer", "Yoga & Pilates", "Cricket Bats"],
        "price_range": (499, 18999),
        "spec_templates": [
            {"frame_material": "High Modulus Graphite", "weight": "4U (80-84g)", "flex": "Medium Stiff", "tension": "24-30 lbs"},
            {"material": "Grade 1 English Willow", "handle": "Sarawak Cane 3-Piece", "edge_profile": "38-40mm", "weight": "1160-1200g"},
            {"material": "High Density Eco TPE", "thickness": "6mm", "grip": "Non-Slip Dual Texture", "dimensions": "183cm x 61cm"}
        ],
        "image": "https://images.unsplash.com/photo-1517649763962-0c623266ddc0?w=800&q=80"
    },
    "Books": {
        "code": "BKS",
        "brands": ["O'Reilly", "Penguin", "HarperCollins", "Pearson", "Packt", "Manning", "Simon & Schuster"],
        "subcategories": ["Computer Science", "Artificial Intelligence", "Business & Finance", "Self-Help", "Science & Fiction"],
        "price_range": (299, 4999),
        "spec_templates": [
            {"format": "Paperback", "pages": "520 Pages", "edition": "3rd Revised Edition", "language": "English", "isbn": "978-0134685991"},
            {"format": "Hardcover", "pages": "380 Pages", "edition": "International Collector's Edition", "language": "English"},
            {"format": "Paperback", "pages": "640 Pages", "publisher": "O'Reilly Media", "language": "English"}
        ],
        "image": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&q=80"
    },
    "Gaming": {
        "code": "GAM",
        "brands": ["Razer", "Logitech G", "Corsair", "SteelSeries", "HyperX", "PlayStation", "Xbox"],
        "subcategories": ["Gaming Mice", "Mechanical Keyboards", "Gaming Headsets", "Controllers", "Gaming Monitors"],
        "price_range": (1299, 45999),
        "spec_templates": [
            {"sensor": "Focus Pro 30K Optical", "polling_rate": "Up to 8000Hz Wireless", "switches": "Optical Gen-3", "weight": "63g"},
            {"switches": "Linear Mechanical Optical Switches", "keycaps": "Double-Shot PBT", "rgb": "Per-Key Chroma RGB", "connectivity": "Detachable Type-C"},
            {"haptics": "Adaptive Triggers + Dual Actuators", "connectivity": "Bluetooth & USB-C", "battery": "1560mAh Built-in"}
        ],
        "image": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800&q=80"
    },
    "Accessories": {
        "code": "ACC",
        "brands": ["Fossil", "Titan", "American Tourister", "Wildcraft", "Tommy Hilfiger", "Casio", "Samsonite"],
        "subcategories": ["Chronograph Watches", "Leather Wallets", "Travel Backpacks", "Trolley Suitcases", "Sunglasses"],
        "price_range": (799, 29999),
        "spec_templates": [
            {"movement": "Japanese Quartz Chronograph", "case_diameter": "42mm", "water_resistance": "5 ATM / 50m", "strap": "Genuine Leather"},
            {"capacity": "32 Litres", "material": "High-Density Water-Repellent Polyester", "laptop_sleeve": "Fits up to 15.6\"", "pockets": "3 Main + 2 Side"},
            {"material": "Full-Grain Top Leather", "slots": "8 Card Slots + 2 Currency Compartments", "rfid_protection": "Yes"}
        ],
        "image": "https://images.unsplash.com/photo-1509741102003-ca64bfe5f069?w=800&q=80"
    }
}

MODELS_POOL = [
    "Pro", "Max", "Ultra", "Elite", "Prime", "Air", "Apex", "Edge", "Vantage", "Signature",
    "Carbon", "Master", "Studio", "Sprint", "Velocity", "Phantom", "Pulse", "Quantum", "Nexus", "Titanium"
]

COLOR_VARIANTS = ["Midnight Black", "Arctic White", "Space Gray", "Ocean Blue", "Forest Green", "Rose Gold", "Graphite"]

def generate_product_record(global_index: int) -> tuple:
    """
    Generates a single coherent, deterministic synthetic product record.
    SKU format: SKU-{CAT}-{BRAND_CODE}-{INDEX:07d} ensures zero collisions across millions of records.
    """
    categories = list(CATEGORY_TAXONOMY.keys())
    cat_name = categories[global_index % len(categories)]
    cat_info = CATEGORY_TAXONOMY[cat_name]

    brand_idx = (global_index // len(categories)) % len(cat_info["brands"])
    brand = cat_info["brands"][brand_idx]

    subcat_idx = (global_index // (len(categories) * len(cat_info["brands"]))) % len(cat_info["subcategories"])
    subcat = cat_info["subcategories"][subcat_idx]

    model_term = MODELS_POOL[(global_index // 3) % len(MODELS_POOL)]
    color = COLOR_VARIANTS[(global_index // 7) % len(COLOR_VARIANTS)]
    series_num = (global_index % 900) + 100

    name = f"{brand} {model_term} {series_num} {subcat} - {color}"

    # Stable, guaranteed unique SKU constraint
    brand_code = "".join(c for c in brand[:3].upper() if c.isalnum()).ljust(3, "X")
    sku = f"SKU-{cat_info['code']}-{brand_code}-{global_index:07d}"

    # Pricing & discounts
    min_p, max_p = cat_info["price_range"]
    price_span = max_p - min_p
    base_price = min_p + ((global_index * 137) % price_span)
    # Round to realistic 99s or 00s
    base_price = float((int(base_price) // 50) * 50 - 1)
    if base_price < min_p:
        base_price = float(min_p)

    discount_percent = (global_index * 17) % 45
    if discount_percent < 5:
        discount_percent = 0
        original_price = base_price
    else:
        original_price = round(base_price / (1.0 - (discount_percent / 100.0)), 2)

    stock = (global_index * 23) % 250 + 5
    rating = round(3.8 + ((global_index * 7) % 12) * 0.1, 1)
    reviews_count = (global_index * 31) % 4800 + 12

    spec_tmpl = cat_info["spec_templates"][global_index % len(cat_info["spec_templates"])].copy()
    spec_tmpl["color"] = color
    spec_tmpl["model_year"] = 2026
    specifications = json.dumps(spec_tmpl)

    description = (
        f"The {name} is engineered by {brand} for high reliability and performance. "
        f"Features premium {color} finish, tested for enterprise standards, backed by manufacturer warranty."
    )

    now_iso = datetime.now().isoformat(timespec="seconds")
    product_img = get_deterministic_product_image(cat_name, subcat, sku)
    gallery_json = json.dumps(get_product_gallery_images(cat_name, subcat, product_img, sku))

    return (
        name,
        brand,
        cat_name,
        subcat,
        description,
        base_price,
        original_price,
        discount_percent,
        stock,
        sku,
        rating,
        reviews_count,
        product_img,
        gallery_json,
        specifications,
        "1 Year Manufacturer Warranty",
        (global_index % 3) + 2,
        "7 Days Replacement / Return",
        "active",
        now_iso,
        now_iso
    )

def bulk_import_catalogue(target_count: int = 1000000, batch_size: int = 25000, progress_callback=None) -> dict:
    """
    High-throughput bulk ingestion pipeline into SQLite.
    Inserts products up to target_count with progress tracking and transaction batching.
    """
    start_time = time.time()
    inserted_total = 0

    conn = get_connection()
    try:
        # Check current count
        current_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        needed = target_count - current_count
        if needed <= 0:
            return {
                "status": "already_satisfied",
                "current_count": current_count,
                "target_count": target_count,
                "elapsed_seconds": 0.0,
                "throughput_records_per_sec": 0
            }

        # High-performance PRAGMAs for bulk ingestion
        conn.execute("PRAGMA synchronous = OFF;")
        conn.execute("PRAGMA journal_mode = MEMORY;")
        conn.execute("PRAGMA cache_size = -128000;")

        start_index = current_count + 1
        batches = (needed + batch_size - 1) // batch_size

        for b in range(batches):
            b_start = start_index + (b * batch_size)
            b_end = min(start_index + needed, b_start + batch_size)
            records = [generate_product_record(i) for i in range(b_start, b_end)]

            conn.executemany("""
                INSERT INTO products (
                    name, brand, category, subcategory, description, price, original_price,
                    discount_percent, stock, sku, rating, review_count, image_url, gallery_images,
                    specifications, warranty, delivery_days, return_policy, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            conn.commit()

            inserted_total += len(records)
            current_total = current_count + inserted_total
            if progress_callback:
                progress_callback(current_total, target_count, inserted_total)
            elif (b + 1) % 4 == 0 or b == batches - 1:
                elapsed = time.time() - start_time
                rps = inserted_total / max(0.01, elapsed)
                print(f"[{b+1}/{batches}] Inserted {current_total:,} / {target_count:,} products ({rps:,.0f} records/sec)")

    finally:
        # Restore safe normal PRAGMAs
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.close()

    total_time = time.time() - start_time
    final_count = get_connection().execute("SELECT COUNT(*) FROM products").fetchone()[0]
    avg_rps = inserted_total / max(0.01, total_time)

    return {
        "status": "completed",
        "initial_count": current_count,
        "inserted_count": inserted_total,
        "final_count": final_count,
        "elapsed_seconds": round(total_time, 2),
        "throughput_records_per_sec": round(avg_rps, 1)
    }

def verify_catalogue_integrity() -> dict:
    """Runs data integrity checks across catalogue database."""
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        distinct_skus = conn.execute("SELECT COUNT(DISTINCT sku) FROM products").fetchone()[0]
        invalid_prices = conn.execute("SELECT COUNT(*) FROM products WHERE price <= 0").fetchone()[0]
        invalid_stocks = conn.execute("SELECT COUNT(*) FROM products WHERE stock < 0").fetchone()[0]
        categories_count = conn.execute("SELECT COUNT(DISTINCT category) FROM products").fetchone()[0]

        is_consistent = (total == distinct_skus) and (invalid_prices == 0) and (invalid_stocks == 0)

        return {
            "total_products": total,
            "unique_skus": distinct_skus,
            "sku_collision_count": total - distinct_skus,
            "invalid_price_records": invalid_prices,
            "invalid_stock_records": invalid_stocks,
            "distinct_categories": categories_count,
            "integrity_passed": is_consistent
        }
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scale catalogue products")
    parser.add_argument("--count", type=int, default=100000, help="Target total products count")
    parser.add_argument("--batch", type=int, default=25000, help="Batch insertion chunk size")
    args = parser.parse_args()

    print(f"Scaling catalogue toward {args.count:,} products...")
    res = bulk_import_catalogue(target_count=args.count, batch_size=args.batch)
    print("Import Result:", res)
    print("Verifying integrity...")
    integ = verify_catalogue_integrity()
    print("Integrity Summary:", integ)

