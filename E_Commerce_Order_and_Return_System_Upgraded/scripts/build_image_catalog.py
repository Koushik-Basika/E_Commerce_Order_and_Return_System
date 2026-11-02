"""
Script to collect, verify, and build data/product_images.json catalog
containing 350+ unique, verified, category-mapped product images.
"""

import os
import sys
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "product_images.json")
CACHE_PATH = os.path.join(DATA_DIR, "image_validation_cache.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def verify_single_url(url: str, timeout: float = 6.0) -> dict:
    """Verifies that URL is reachable, returns image content-type and valid image bytes."""
    if not url or not url.startswith(("http://", "https://")):
        return {"valid": False, "error": "Invalid URL protocol"}

    try:
        # Request first 1024 bytes using Range header to save bandwidth
        req_headers = dict(HEADERS)
        req_headers["Range"] = "bytes=0-1023"
        r = requests.get(url, headers=req_headers, timeout=timeout, allow_redirects=True, stream=True)
        
        # If server does not support Range, status is 200; if it supports Range, status is 206
        if r.status_code not in (200, 206, 304):
            return {"valid": False, "status_code": r.status_code, "error": f"HTTP status {r.status_code}"}

        ctype = r.headers.get("Content-Type", "").lower()
        if not (ctype.startswith("image/") or "octet-stream" in ctype or "binary" in ctype):
            return {"valid": False, "status_code": r.status_code, "error": f"Invalid content type: {ctype}"}

        chunk = r.raw.read(1024)
        if len(chunk) < 4:
            return {"valid": False, "error": "Empty or truncated response"}

        # Validate magic numbers
        is_jpeg = chunk.startswith(b"\xff\xd8\xff")
        is_png = chunk.startswith(b"\x89PNG\r\n\x1a\n")
        is_webp = chunk.startswith(b"RIFF") and b"WEBP" in chunk[:16]
        is_gif = chunk.startswith((b"GIF87a", b"GIF89a"))
        is_svg = b"<svg" in chunk.lower()

        if not (is_jpeg or is_png or is_webp or is_gif or is_svg or ctype.startswith("image/")):
            return {"valid": False, "error": "Unrecognized image binary header"}

        actual_format = "image/jpeg" if is_jpeg else ("image/png" if is_png else ("image/webp" if is_webp else ("image/gif" if is_gif else ctype)))

        return {
            "valid": True,
            "status_code": r.status_code,
            "content_type": actual_format,
            "bytes_received": len(chunk)
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

def fetch_dummyjson_images():
    """Fetches high-quality product images from DummyJSON API."""
    print("[*] Fetching DummyJSON product catalog...")
    category_map = {
        "smartphones": ("Mobiles", "5G Smartphones"),
        "mobile-accessories": ("Mobiles", "Mobile Accessories"),
        "laptops": ("Laptops", "Ultrabooks"),
        "tablets": ("Laptops", "2-in-1 Touch Laptops"),
        "beauty": ("Beauty", "Face Serums"),
        "skin-care": ("Beauty", "Moisturizers"),
        "fragrances": ("Beauty", "Fragrances"),
        "mens-shirts": ("Fashion", "Slim Fit Shirts"),
        "tops": ("Fashion", "Cotton Polos"),
        "womens-dresses": ("Fashion", "Ethnic Wear"),
        "mens-shoes": ("Footwear", "Formal Leather Shoes"),
        "womens-shoes": ("Footwear", "Lifestyle Sneakers"),
        "mens-watches": ("Accessories", "Chronograph Watches"),
        "womens-watches": ("Accessories", "Chronograph Watches"),
        "sunglasses": ("Accessories", "Sunglasses"),
        "womens-bags": ("Accessories", "Travel Backpacks"),
        "womens-jewellery": ("Accessories", "Wallets & Watches"),
        "kitchen-accessories": ("Home & Kitchen", "Coffee Makers"),
        "furniture": ("Home & Kitchen", "Home Decor & Furnishing"),
        "home-decoration": ("Home & Kitchen", "Home Decor & Furnishing"),
        "sports-accessories": ("Sports", "Fitness Equipment")
    }

    results = []
    try:
        r = requests.get("https://dummyjson.com/products?limit=0", headers=HEADERS, timeout=12)
        if r.status_code == 200:
            products = r.json().get("products", [])
            for p in products:
                raw_cat = p.get("category", "")
                if raw_cat in category_map:
                    mapped_cat, mapped_subcat = category_map[raw_cat]
                    thumb = p.get("thumbnail")
                    images = p.get("images", [])
                    title = p.get("title", "")
                    
                    if thumb:
                        results.append({
                            "url": thumb,
                            "category": mapped_cat,
                            "subcategory": mapped_subcat,
                            "title": title,
                            "provider": "DummyJSON",
                            "gallery_urls": [img for img in images if img != thumb][:3]
                        })
                    for img in images:
                        if img != thumb:
                            results.append({
                                "url": img,
                                "category": mapped_cat,
                                "subcategory": mapped_subcat,
                                "title": f"{title} (Angle)",
                                "provider": "DummyJSON",
                                "gallery_urls": [thumb]
                            })
        print(f"[+] Retrieved {len(results)} candidate image entries from DummyJSON.")
    except Exception as e:
        print(f"[-] DummyJSON fetch failed: {e}")
    return results

def fetch_openlibrary_covers():
    """Fetches verified book cover images from Open Library."""
    print("[*] Fetching OpenLibrary book covers...")
    subjects = [
        ("computer_science", "Books", "Computer Science"),
        ("artificial_intelligence", "Books", "Artificial Intelligence"),
        ("business", "Books", "Business & Finance"),
        ("psychology", "Books", "Self-Help"),
        ("science_fiction", "Books", "Science & Fiction")
    ]
    results = []
    for sub, cat, subcat in subjects:
        try:
            url = f"https://openlibrary.org/subjects/{sub}.json?limit=12"
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                works = r.json().get("works", [])
                for w in works:
                    cov_id = w.get("cover_id")
                    title = w.get("title", "Book")
                    if cov_id:
                        img_url = f"https://covers.openlibrary.org/b/id/{cov_id}-L.jpg"
                        results.append({
                            "url": img_url,
                            "category": cat,
                            "subcategory": subcat,
                            "title": title,
                            "provider": "OpenLibrary",
                            "gallery_urls": [f"https://covers.openlibrary.org/b/id/{cov_id}-M.jpg"]
                        })
        except Exception as e:
            print(f"[-] OpenLibrary fetch failed for {sub}: {e}")
    print(f"[+] Retrieved {len(results)} candidate image entries from OpenLibrary.")
    return results

def fetch_wikimedia_images():
    """Fetches high-quality CC / Public Domain images from Wikimedia Commons."""
    print("[*] Fetching Wikimedia Commons images...")
    queries = [
        ("gaming mouse", "Gaming", "Gaming Mice"),
        ("mechanical keyboard", "Gaming", "Mechanical Keyboards"),
        ("gaming headset", "Gaming", "Gaming Headsets"),
        ("game controller", "Gaming", "Controllers"),
        ("gamepad", "Gaming", "Controllers"),
        ("gaming monitor", "Gaming", "Gaming Monitors"),
        ("wireless headphones", "Electronics", "Wireless Headphones"),
        ("wireless earbuds", "Electronics", "Earbuds & TWS"),
        ("smartwatch", "Electronics", "Smartwatches"),
        ("bluetooth speaker", "Electronics", "Bluetooth Speakers"),
        ("soundbar", "Electronics", "Soundbars"),
        ("badminton racket", "Sports", "Badminton Rackets"),
        ("cricket bat", "Sports", "Cricket Bats"),
        ("football ball", "Sports", "Football & Soccer"),
        ("gym dumbbell", "Sports", "Fitness Equipment"),
        ("yoga mat", "Sports", "Yoga & Pilates")
    ]
    results = []
    for q, cat, subcat in queries:
        try:
            url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=filetype:bitmap+{q}&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url|mime|size&format=json"
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                pages = r.json().get("query", {}).get("pages", {})
                for p in pages.values():
                    info = p.get("imageinfo", [{}])[0]
                    img_url = info.get("url")
                    mime = info.get("mime", "")
                    title = p.get("title", "").replace("File:", "")
                    if img_url and ("image/jpeg" in mime or "image/png" in mime or "image/webp" in mime):
                        # Avoid huge TIFF or gigantic raw files (>15MB)
                        size = info.get("size", 0)
                        if size < 15 * 1024 * 1024:
                            results.append({
                                "url": img_url,
                                "category": cat,
                                "subcategory": subcat,
                                "title": title[:60],
                                "provider": "Wikimedia Commons",
                                "gallery_urls": []
                            })
        except Exception as e:
            print(f"[-] Wikimedia query failed for {q}: {e}")
    print(f"[+] Retrieved {len(results)} candidate image entries from Wikimedia Commons.")
    return results

def get_curated_unsplash_images():
    """Returns curated direct Unsplash image URLs across categories."""
    raw_list = [
        # Electronics
        ("https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80", "Electronics", "Wireless Headphones", "Sony Noise Cancelling Headphones"),
        ("https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800&q=80", "Electronics", "Wireless Headphones", "Bose Wireless Headphones"),
        ("https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800&q=80", "Electronics", "Earbuds & TWS", "Wireless Earbuds with Case"),
        ("https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800&q=80", "Electronics", "Bluetooth Speakers", "Compact Bluetooth Speaker"),
        ("https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80", "Electronics", "Smartwatches", "Minimalist Smart Watch"),
        ("https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=800&q=80", "Electronics", "Smartwatches", "Apple Watch Sport Band"),
        ("https://images.unsplash.com/photo-1543512214-318c7553f230?w=800&q=80", "Electronics", "Bluetooth Speakers", "Studio Audio Speaker"),
        ("https://images.unsplash.com/photo-1545454675-3531b543be5d?w=800&q=80", "Electronics", "Soundbars", "Home Theater Audio Speaker"),
        ("https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800&q=80", "Electronics", "Wireless Headphones", "Studio Reference Audio Monitors"),
        ("https://images.unsplash.com/photo-1583394838336-acd977736f90?w=800&q=80", "Electronics", "Wireless Headphones", "Over-Ear Wireless Headset"),
        ("https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=800&q=80", "Electronics", "Earbuds & TWS", "In-Ear HiFi Earphones"),
        ("https://images.unsplash.com/photo-1588423771073-b8903fbb85b5?w=800&q=80", "Electronics", "Bluetooth Speakers", "Acoustic Home Speaker"),
        ("https://images.unsplash.com/photo-1577174881658-0f30ed549adc?w=800&q=80", "Electronics", "Smartwatches", "Digital Fitness Smartwatch"),
        ("https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=800&q=80", "Electronics", "Smartwatches", "Modern Smart Fitness Watch"),
        ("https://images.unsplash.com/photo-1589003077984-894e133dabab?w=800&q=80", "Electronics", "Earbuds & TWS", "True Wireless Earbuds Pods"),
        ("https://images.unsplash.com/photo-1598331668826-20cecc596b86?w=800&q=80", "Electronics", "Bluetooth Speakers", "Waterproof Outdoor Speaker"),
        ("https://images.unsplash.com/photo-1524678606370-a47ad25cb82a?w=800&q=80", "Electronics", "Wireless Headphones", "Foldable Bluetooth Headphones"),

        # Mobiles
        ("https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80", "Mobiles", "5G Smartphones", "iPhone Flagship Smartphone"),
        ("https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800&q=80", "Mobiles", "5G Smartphones", "Modern Android Smartphone"),
        ("https://images.unsplash.com/photo-1567581935884-3349723552ca?w=800&q=80", "Mobiles", "Flagship Phones", "Smartphone Triple Camera"),
        ("https://images.unsplash.com/photo-1580910051074-3eb694886505?w=800&q=80", "Mobiles", "Budget Phones", "Budget Smartphone with Glass Back"),
        ("https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=800&q=80", "Mobiles", "Foldable Phones", "Frameless OLED Smartphone"),
        ("https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800&q=80", "Mobiles", "Mobile Accessories", "Smartphone Screen & Case"),
        ("https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=800&q=80", "Mobiles", "5G Smartphones", "Silver Slim Smartphone"),
        ("https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?w=800&q=80", "Mobiles", "Mobile Accessories", "Wireless Phone Charging Pad"),

        # Laptops
        ("https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80", "Laptops", "Ultrabooks", "MacBook Pro Aluminum Laptop"),
        ("https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80", "Laptops", "Ultrabooks", "Thin Bezel Business Laptop"),
        ("https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800&q=80", "Laptops", "Business Laptops", "Dell Professional Workstation Laptop"),
        ("https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=800&q=80", "Laptops", "Gaming Laptops", "High Performance Gaming Laptop"),
        ("https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&q=80", "Laptops", "2-in-1 Touch Laptops", "Laptop on Minimal Wooden Desk"),
        ("https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&q=80", "Laptops", "Monitors & Accessories", "4K Ultra-Wide Desktop Monitor"),
        ("https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800&q=80", "Laptops", "Ultrabooks", "Slim Ultrabook on Workspace"),

        # Fashion
        ("https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&q=80", "Fashion", "Slim Fit Shirts", "White Cotton Designer T-Shirt"),
        ("https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800&q=80", "Fashion", "Cotton Polos", "Men's Casual Button-Up Shirt"),
        ("https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=800&q=80", "Fashion", "Denim Jeans", "Classic Slim Denim Jeans"),
        ("https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=800&q=80", "Fashion", "Denim Jeans", "Vintage Distressed Blue Jeans"),
        ("https://images.unsplash.com/photo-1548883354-7622d03aca27?w=800&q=80", "Fashion", "Denim Jeans", "Dark Wash Straight Leg Denim"),
        ("https://images.unsplash.com/photo-1562157873-818bc0726f68?w=800&q=80", "Fashion", "Denim Jeans", "Modern Casual Denim Pants"),
        ("https://images.unsplash.com/photo-1584370848010-d7fe6bc767ec?w=800&q=80", "Fashion", "Denim Jeans", "High-Waist Tapered Fit Jeans"),
        ("https://images.unsplash.com/photo-1582418702059-97ebafb35d09?w=800&q=80", "Fashion", "Denim Jeans", "Classic Indigo Stonewash Jeans"),
        ("https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=800&q=80", "Fashion", "Denim Jeans", "Urban Fit Denim Trousers"),
        ("https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&q=80", "Fashion", "Cotton Polos", "Black Heavyweight Graphic Tee"),
        ("https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800&q=80", "Fashion", "Slim Fit Shirts", "Premium Heather Grey T-Shirt"),
        ("https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&q=80", "Fashion", "Jackets & Blazers", "Leather Biker Jacket"),
        ("https://images.unsplash.com/photo-1544441893-675973e31985?w=800&q=80", "Fashion", "Jackets & Blazers", "Wool Trench Coat"),
        ("https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=800&q=80", "Fashion", "Ethnic Wear", "Autumn Casual Apparel"),

        # Footwear
        ("https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80", "Footwear", "Running Shoes", "Nike Red Performance Sneaker"),
        ("https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&q=80", "Footwear", "Lifestyle Sneakers", "Puma Retro White Sneakers"),
        ("https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=800&q=80", "Footwear", "Lifestyle Sneakers", "Vans Classic Canvas Sneakers"),
        ("https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=800&q=80", "Footwear", "Formal Leather Shoes", "Handcrafted Oxford Leather Shoes"),
        ("https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=800&q=80", "Footwear", "Training Shoes", "Air Cushion Athletic Trainers"),
        ("https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?w=800&q=80", "Footwear", "Running Shoes", "Blue Lightweight Running Shoes"),
        ("https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800&q=80", "Footwear", "Formal Leather Shoes", "Brown Leather Derby Shoes"),

        # Home & Kitchen
        ("https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=800&q=80", "Home & Kitchen", "Coffee Makers", "Espresso Coffee Machine"),
        ("https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=800&q=80", "Home & Kitchen", "Air Fryers", "Electric Kitchen Appliances"),
        ("https://images.unsplash.com/photo-1585659722983-3a675dabf23d?w=800&q=80", "Home & Kitchen", "Mixer Grinders", "Modern Kitchen Blender"),
        ("https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&q=80", "Home & Kitchen", "Cookware Sets", "Ceramic Cookware & Pots"),
        ("https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=800&q=80", "Home & Kitchen", "Home Decor & Furnishing", "Minimalist Kitchen Counter Decor"),
        ("https://images.unsplash.com/photo-1544816155-12df9643f363?w=800&q=80", "Home & Kitchen", "Cookware Sets", "Stainless Steel Induction Kettle"),

        # Beauty
        ("https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800&q=80", "Beauty", "Face Serums", "Vitamin C Facial Serum"),
        ("https://images.unsplash.com/photo-1571781926291-c477ebfd024b?w=800&q=80", "Beauty", "Moisturizers", "Hydrating Facial Cream Jar"),
        ("https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&q=80", "Beauty", "Sunscreen & SPF", "Mineral Sunscreen Lotion"),
        ("https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=800&q=80", "Beauty", "Fragrances", "Luxury Eau de Parfum Glass Bottle"),
        ("https://images.unsplash.com/photo-1608248597359-54890637171e?w=800&q=80", "Beauty", "Hair Cleansers", "Organic Argan Oil Shampoo"),
        ("https://images.unsplash.com/photo-1512290900672-1f0236a94593?w=800&q=80", "Beauty", "Fragrances", "French Perfume Spray"),

        # Sports
        ("https://images.unsplash.com/photo-1517649763962-0c623266ddc0?w=800&q=80", "Sports", "Football & Soccer", "Official Match Soccer Ball"),
        ("https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=800&q=80", "Sports", "Fitness Equipment", "Cast Iron Hex Dumbbells"),
        ("https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&q=80", "Sports", "Fitness Equipment", "Gym Fitness Weights & Rack"),
        ("https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800&q=80", "Sports", "Yoga & Pilates", "Eco Non-Slip Yoga Mat"),
        ("https://images.unsplash.com/photo-1622163642998-1ea32b0bbc67?w=800&q=80", "Sports", "Badminton Rackets", "Carbon Fiber Badminton Racket"),
        ("https://images.unsplash.com/photo-1530549387789-4c1017266635?w=800&q=80", "Sports", "Fitness Equipment", "Athletic Resistance Bands"),
        ("https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800&q=80", "Sports", "Fitness Equipment", "Athletic Running Gear"),
        ("https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=800&q=80", "Sports", "Fitness Equipment", "Crossfit Gym Training Setup"),
        ("https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=800&q=80", "Sports", "Fitness Equipment", "Chrome Free Weights Dumbbells"),
        ("https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=800&q=80", "Sports", "Badminton Rackets", "Tournament Badminton Gear"),
        ("https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=800&q=80", "Sports", "Cricket Bats", "Cricket Sports Equipment"),
        ("https://images.unsplash.com/photo-1575052814086-f385e2e2ad1b?w=800&q=80", "Sports", "Yoga & Pilates", "Stretching Yoga Pose Mat"),
        ("https://images.unsplash.com/photo-1526506118085-60ce8714f8c5?w=800&q=80", "Sports", "Fitness Equipment", "Heavy Barbell Training"),
        ("https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&q=80", "Sports", "Fitness Equipment", "Gym Barbell & Weights"),
        ("https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80", "Sports", "Fitness Equipment", "Personal Fitness Training Gear"),
        ("https://images.unsplash.com/photo-1599058945522-28d584b6f0ff?w=800&q=80", "Sports", "Fitness Equipment", "Athletic High Performance Workout"),
        ("https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=800&q=80", "Sports", "Fitness Equipment", "Kettlebell Conditioning"),
        ("https://images.unsplash.com/photo-1574680178050-55c6a6a96e0a?w=800&q=80", "Sports", "Fitness Equipment", "Bodybuilder Weight Training"),

        # Gaming
        ("https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800&q=80", "Gaming", "Gaming Mice", "Optical RGB Gaming Mouse"),
        ("https://images.unsplash.com/photo-1612287233207-6b22987a0201?w=800&q=80", "Gaming", "Mechanical Keyboards", "Backlit Mechanical Gaming Keyboard"),
        ("https://images.unsplash.com/photo-1600080972464-8e5f35f63d08?w=800&q=80", "Gaming", "Controllers", "Wireless Dual-Vibration Gamepad"),
        ("https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&q=80", "Gaming", "Gaming Headsets", "Surround Sound Gaming Headset"),
        ("https://images.unsplash.com/photo-1593305841991-05c297ba4575?w=800&q=80", "Gaming", "Gaming Monitors", "Esports Gaming Rig & Monitor"),
        ("https://images.unsplash.com/photo-1592840496694-26d035b52b48?w=800&q=80", "Gaming", "Controllers", "Console Gaming Controller"),
        ("https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&q=80", "Gaming", "Gaming Monitors", "Pro Esports Battlestation"),
        ("https://images.unsplash.com/photo-1563089145-599997674d42?w=800&q=80", "Gaming", "Gaming Mice", "Ergonomic Optical Gaming Mouse"),
        ("https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=800&q=80", "Gaming", "Controllers", "Next-Gen Wireless Controller"),
        ("https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800&q=80", "Gaming", "Controllers", "Retro Arcade Joystick Gamepad"),
        ("https://images.unsplash.com/photo-1616588589676-62b3bd4ff6d2?w=800&q=80", "Gaming", "Mechanical Keyboards", "Tenkeyless RGB Gaming Keyboard"),
        ("https://images.unsplash.com/photo-1618788372246-79faff0c3742?w=800&q=80", "Gaming", "Gaming Headsets", "High-Fidelity Gaming Headset with Mic"),
        ("https://images.unsplash.com/photo-1579373903781-fd5c0c30c4cd?w=800&q=80", "Gaming", "Gaming Mice", "Precision Optical Mouse"),
        ("https://images.unsplash.com/photo-1606813907291-d86efa9b94db", "Gaming", "Controllers", "DualSense Wireless Controller"),
        ("https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=800&q=80", "Gaming", "Gaming Headsets", "Pro Gaming Wireless Audio"),
        ("https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=800&q=80", "Gaming", "Mechanical Keyboards", "Custom Mechanical Switch Keyboard"),
        ("https://images.unsplash.com/photo-1580234811497-9df7fd2f357e?w=800&q=80", "Gaming", "Controllers", "White Wireless Game Controller"),
        ("https://images.unsplash.com/photo-1542751110-97427bbecf20?w=800&q=80", "Gaming", "Gaming Monitors", "Pro Gamer Desktop Gaming Display"),
        ("https://images.unsplash.com/photo-1560253023-3ec5d502959f?w=800&q=80", "Gaming", "Mechanical Keyboards", "Gaming RGB Backlit Mechanical Board"),
        ("https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800&q=80", "Gaming", "Controllers", "Retro Console Gamepad Controller"),
        ("https://images.unsplash.com/photo-1526509867162-5b0c0d1b4b33?w=800&q=80", "Gaming", "Gaming Headsets", "Stereo Gaming Headset Surround Sound"),

        # Electronics (Extra)
        ("https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800&q=80", "Electronics", "Wireless Headphones", "Hi-Fi Desk Audio Setup"),
        ("https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=800&q=80", "Electronics", "Bluetooth Speakers", "Vintage Style Audio Speaker"),
        ("https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=800&q=80", "Electronics", "Wireless Headphones", "Over-Ear Premium Sound"),
        ("https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800&q=80", "Electronics", "Soundbars", "Modern TV Soundbar Bar"),
        ("https://images.unsplash.com/photo-1468495244123-6c6c332eeece?w=800&q=80", "Electronics", "Smartwatches", "Tech Gadget Devices"),
        ("https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=800&q=80", "Electronics", "Earbuds & TWS", "Matte Black Earbuds"),
        ("https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=800&q=80", "Electronics", "Wireless Headphones", "Studio DJ Audio Headset"),
        ("https://images.unsplash.com/photo-1615655406736-b37c4fabf923?w=800&q=80", "Electronics", "Smartwatches", "Waterproof Smart Sports Tracker"),
        ("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&q=80", "Electronics", "Bluetooth Speakers", "Party Bluetooth Sound Box"),
        ("https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=800&q=80", "Electronics", "Smartwatches", "Ultra Slim Smart Band"),

        # Accessories
        ("https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80", "Accessories", "Travel Backpacks", "Water-Repellent Commuter Backpack"),
        ("https://images.unsplash.com/photo-1627123424574-724758594e93?w=800&q=80", "Accessories", "Leather Wallets", "Genuine Leather Bifold Wallet"),
        ("https://images.unsplash.com/photo-1509741102003-ca64bfe5f069?w=800&q=80", "Accessories", "Sunglasses", "Classic Polarized Sunglasses"),
        ("https://images.unsplash.com/photo-1622434641406-a158123450f9?w=800&q=80", "Accessories", "Chronograph Watches", "Luxury Analog Chronograph Watch"),
        ("https://images.unsplash.com/photo-1565084888279-aca607ecce0c?w=800&q=80", "Accessories", "Trolley Suitcases", "Hardshell Spinner Suitcase")
    ]
    return [
        {
            "url": item[0],
            "category": item[1],
            "subcategory": item[2],
            "title": item[3],
            "provider": "Unsplash",
            "gallery_urls": []
        }
        for item in raw_list
    ]

def build_catalog():
    print("=" * 70)
    print("BUILDING 300+ UNIQUE VERIFIED PRODUCT IMAGE CATALOG")
    print("=" * 70)

    # 1. Collect all candidate images
    candidates = []
    candidates.extend(get_curated_unsplash_images())
    candidates.extend(fetch_dummyjson_images())
    candidates.extend(fetch_openlibrary_covers())
    candidates.extend(fetch_wikimedia_images())

    print(f"[*] Total raw candidates gathered: {len(candidates)}")

    # Deduplicate strictly by URL
    unique_candidates = {}
    for item in candidates:
        url = item["url"].strip()
        if url and url not in unique_candidates:
            unique_candidates[url] = item

    print(f"[*] Unique candidate URLs to verify: {len(unique_candidates)}")

    # 2. Multithreaded Verification with Smart Existing Cache
    cached_verified = {}
    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                for entry in json.load(f):
                    cached_verified[entry["url"]] = entry
        except Exception:
            pass

    urls_to_verify = [u for u in unique_candidates if u not in cached_verified]
    print(f"[*] Previously verified URLs cached: {len(cached_verified)}, new URLs to verify: {len(urls_to_verify)}", flush=True)

    verified_entries = [cached_verified[u] for u in unique_candidates if u in cached_verified]
    broken_urls = []

    # Map cat code
    cat_codes = {
        "Electronics": "elec", "Mobiles": "mob", "Laptops": "lap",
        "Fashion": "fash", "Footwear": "foot", "Home & Kitchen": "home",
        "Beauty": "beau", "Sports": "spt", "Books": "book",
        "Gaming": "game", "Accessories": "acc"
    }

    if urls_to_verify:
        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_url = {executor.submit(verify_single_url, url): url for url in urls_to_verify}
            completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                completed += 1
                if completed % 20 == 0 or completed == len(urls_to_verify):
                    print(f"    Progress: {completed}/{len(urls_to_verify)} checked...", flush=True)
                try:
                    res = future.result()
                    if res.get("valid"):
                        item = unique_candidates[url]
                        item["verified"] = True
                        item["content_type"] = res.get("content_type", "image/jpeg")
                        item["status_code"] = res.get("status_code", 200)
                        verified_entries.append(item)
                    else:
                        broken_urls.append((url, res.get("error")))
                except Exception as e:
                    broken_urls.append((url, str(e)))

    print(f"[+] Validation complete: {len(verified_entries)} total URLs verified valid, {len(broken_urls)} new broken.", flush=True)

    # 3. Assign deterministic unique IDs and format final catalog entries
    cat_counters = {}
    catalog = []
    for item in verified_entries:
        cat = item["category"]
        code = cat_codes.get(cat, "gen")
        idx = cat_counters.get(cat, 1)
        cat_counters[cat] = idx + 1
        
        entry = {
            "id": f"img_{code}_{idx:03d}",
            "url": item["url"],
            "category": cat,
            "subcategory": item.get("subcategory", "General"),
            "title": item.get("title", ""),
            "provider": item.get("provider", "Verified Public Source"),
            "verified": True,
            "content_type": item.get("content_type", "image/jpeg"),
            "gallery_urls": item.get("gallery_urls", [])
        }
        catalog.append(entry)

    # 4. Save to product_images.json
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    # Save validation cache
    cache_data = {
        "verified_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_verified": len(catalog),
        "total_broken": len(broken_urls),
        "broken_urls": broken_urls[:20],
        "category_breakdown": {cat: cat_counters.get(cat, 0) - 1 for cat in cat_codes}
    }
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)

    print("=" * 70)
    print("IMAGE CATALOG GENERATION REPORT:")
    print(f"Total Unique Verified Image URLs: {len(catalog)}")
    for cat, count in sorted(cache_data["category_breakdown"].items()):
        print(f"  • {cat.ljust(16)}: {count} verified images")
    print(f"Manifest written to: {OUTPUT_PATH}")
    print("=" * 70)
    return len(catalog)

if __name__ == "__main__":
    count = build_catalog()
    if count < 300:
        print(f"[ERROR] Only {count} images verified. Need >= 300!")
        sys.exit(1)
    else:
        print(f"[SUCCESS] Catalog meets minimum requirements: {count} >= 300 distinct URLs!")
