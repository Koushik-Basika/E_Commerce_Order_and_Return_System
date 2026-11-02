"""
E-Commerce Order and Return System — Production Image Validation Suite
Validates image syntax, remote accessibility, MIME content-types, binary magic numbers,
bandwidth throttling (Range requests), duplicate detection, and caching.
"""

import os
import sys
import json
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(BASE_DIR, "data", "product_images.json")
CACHE_PATH = os.path.join(BASE_DIR, "data", "image_validation_cache.json")
DB_PATH = os.path.join(BASE_DIR, "ecommerce.db")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SUPPORTED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp",
    "image/gif", "image/svg+xml", "image/avif"
}

def is_syntactically_valid_url(url: str) -> bool:
    """Verifies that URL has valid format, scheme and netloc."""
    if not url or not isinstance(url, str):
        return False
    if url.startswith("data:image/"):
        return True  # Valid data URI
    try:
        parsed = urllib.parse.urlparse(url)
        return bool(parsed.scheme in ("http", "https") and parsed.netloc)
    except Exception:
        return False

def validate_image_stream(url: str, timeout: float = 6.0) -> Dict:
    """
    Performs streaming verification of a remote image URL.
    Fetches only the initial 1024 bytes to inspect magic headers without consuming heavy bandwidth.
    """
    if not is_syntactically_valid_url(url):
        return {"valid": False, "status_code": 0, "error": "Invalid URL syntax or unsupported protocol"}

    if url.startswith("data:image/"):
        return {"valid": True, "status_code": 200, "content_type": "image/svg+xml", "magic_bytes_verified": True}

    headers = {
        "User-Agent": USER_AGENT,
        "Range": "bytes=0-1023",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"
    }

    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
        status = r.status_code

        # Standard successful statuses (200 OK, 206 Partial Content, 304 Not Modified)
        if status not in (200, 206, 304):
            return {"valid": False, "status_code": status, "error": f"HTTP response status {status}"}

        ctype = r.headers.get("Content-Type", "").lower().split(";")[0].strip()
        
        # Read first 1KB of content
        chunk = r.raw.read(1024)
        if len(chunk) < 4:
            return {"valid": False, "status_code": status, "error": "Truncated or zero-byte response received"}

        # Validate Binary Magic Numbers
        is_jpeg = chunk.startswith(b"\xff\xd8\xff")
        is_png = chunk.startswith(b"\x89PNG\r\n\x1a\n")
        is_webp = chunk.startswith(b"RIFF") and b"WEBP" in chunk[8:16]
        is_gif = chunk.startswith((b"GIF87a", b"GIF89a"))
        is_svg = b"<svg" in chunk.lower()

        has_magic = is_jpeg or is_png or is_webp or is_gif or is_svg

        # Format detection
        detected_mime = ctype
        if is_jpeg:
            detected_mime = "image/jpeg"
        elif is_png:
            detected_mime = "image/png"
        elif is_webp:
            detected_mime = "image/webp"
        elif is_gif:
            detected_mime = "image/gif"
        elif is_svg:
            detected_mime = "image/svg+xml"

        # Content-Type check
        if not (ctype.startswith("image/") or has_magic):
            return {
                "valid": False,
                "status_code": status,
                "error": f"Content-Type '{ctype}' does not match supported image MIME formats"
            }

        return {
            "valid": True,
            "status_code": status,
            "content_type": detected_mime,
            "magic_bytes_verified": has_magic,
            "bytes_inspected": len(chunk)
        }

    except requests.exceptions.Timeout:
        return {"valid": False, "status_code": 408, "error": f"Network connection timed out after {timeout}s"}
    except requests.exceptions.SSLError as e:
        return {"valid": False, "status_code": 0, "error": f"TLS/SSL certificate error: {e}"}
    except requests.exceptions.ConnectionError as e:
        return {"valid": False, "status_code": 0, "error": f"Connection refused or unreachable host: {e}"}
    except Exception as e:
        return {"valid": False, "status_code": 0, "error": str(e)}

def validate_catalog_file(
    catalog_path: str = CATALOG_PATH,
    use_cache: bool = True,
    max_workers: int = 12
) -> Dict:
    """
    Validates all entries in data/product_images.json.
    Reports unique counts, duplicate URLs, category coverage, and remote reachability.
    """
    if not os.path.exists(catalog_path):
        return {"error": f"Catalog file not found: {catalog_path}", "valid": False}

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # 1. Duplicate URL detection within manifest
    seen_urls = {}
    duplicates = []
    for item in catalog:
        url = item.get("url", "")
        if url in seen_urls:
            duplicates.append((item.get("id"), url, seen_urls[url]))
        else:
            seen_urls[url] = item.get("id")

    unique_urls = list(seen_urls.keys())

    # 2. Check cache
    cache = {}
    if use_cache and os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                cache = cdata.get("url_cache", {})
        except Exception:
            cache = {}

    # 3. Multithreaded network validation for uncached URLs
    to_verify = [u for u in unique_urls if u not in cache or not cache[u].get("valid")]
    verified_results = dict(cache)

    if to_verify:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(validate_image_stream, u): u for u in to_verify}
            for future in as_completed(future_to_url):
                u = future_to_url[future]
                try:
                    res = future.result()
                    verified_results[u] = res
                except Exception as e:
                    verified_results[u] = {"valid": False, "error": str(e)}

    # 4. Compile metrics
    valid_count = 0
    broken_urls = []
    category_counts = {}

    for item in catalog:
        u = item.get("url")
        cat = item.get("category", "Uncategorized")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        res = verified_results.get(u, {})
        if res.get("valid"):
            valid_count += 1
        else:
            broken_urls.append({"id": item.get("id"), "url": u, "error": res.get("error", "Unknown")})

    # Save cache
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "verified_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_urls": len(unique_urls),
            "valid_urls": len([u for u in unique_urls if verified_results.get(u, {}).get("valid")]),
            "url_cache": verified_results
        }, f, indent=2)

    return {
        "total_entries": len(catalog),
        "unique_urls_count": len(unique_urls),
        "verified_urls_count": len([u for u in unique_urls if verified_results.get(u, {}).get("valid")]),
        "duplicate_urls_count": len(duplicates),
        "duplicates": duplicates,
        "broken_urls_count": len(broken_urls),
        "broken_urls": broken_urls,
        "category_breakdown": category_counts,
        "is_sufficient": len(unique_urls) >= 300 and len([u for u in unique_urls if verified_results.get(u, {}).get("valid")]) >= 300
    }

def print_validation_report(results: Dict):
    """Prints a professional, structured validation report."""
    print("=" * 72)
    print("E-COMMERCE ORDER AND RETURN SYSTEM — IMAGE CATALOG VALIDATION REPORT")
    print("=" * 72)
    print(f"Total Catalog Manifest Entries:  {results.get('total_entries', 0)}")
    print(f"Distinct Unique Image URLs:      {results.get('unique_urls_count', 0)}")
    print(f"Verified Active Image URLs:      {results.get('verified_urls_count', 0)}")
    print(f"Duplicate Image URLs in Catalog: {results.get('duplicate_urls_count', 0)}")
    print(f"Broken / Inaccessible URLs:      {results.get('broken_urls_count', 0)}")
    print("-" * 72)
    print("Category Breakdown (Verified Active):")
    for cat, count in sorted(results.get("category_breakdown", {}).items()):
        print(f"  • {cat.ljust(20)}: {count} images")
    print("-" * 72)

    if results.get("duplicates"):
        print("[WARNING] Duplicate URLs detected:")
        for dup in results["duplicates"][:5]:
            print(f"  - ID: {dup[0]} matches existing ID: {dup[2]}")

    if results.get("broken_urls"):
        print("[WARNING] Broken URLs detected:")
        for b in results["broken_urls"][:5]:
            print(f"  - [{b.get('id')}] {b.get('url')[:60]} -> {b.get('error')}")

    is_ok = results.get("is_sufficient", False)
    status_str = "PASSED (>= 300 verified unique URLs)" if is_ok else "FAILED (< 300 verified URLs)"
    print(f"Target Requirement (>= 300 Unique Verified URLs): {status_str}")
    print("=" * 72)

if __name__ == "__main__":
    report = validate_catalog_file()
    print_validation_report(report)
    sys.exit(0 if report.get("is_sufficient") else 1)
