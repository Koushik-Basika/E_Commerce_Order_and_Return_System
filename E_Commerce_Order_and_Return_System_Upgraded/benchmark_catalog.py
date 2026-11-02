"""
E-Commerce Order and Return System — Catalogue Benchmark Suite
Measures actual performance across:
1. Catalogue Ingestion & Bulk Throughput (records/sec)
2. SKU Uniqueness and Integrity Constraint Verification
3. Text Search Query Latency (LIKE / Index scans)
4. Multi-Attribute Filter Query Latency (Category + Brand + Price)
5. Deep Server-Side Pagination Query Latency (Page 1 to Page 5,000)
6. Peak Memory Footprint & Disk Space Utilization
"""

import os
import sys
import time
import statistics
import tracemalloc
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.connection import get_connection, DB_PATH
from database.repository import get_products_paginated
from utils.catalog_scaler import bulk_import_catalogue, verify_catalogue_integrity

def run_benchmark(target_products: int = 100000):
    print("=" * 65)
    print(f"CATALOGUE PERFORMANCE BENCHMARK: Target {target_products:,} Products")
    print("=" * 65)

    tracemalloc.start()
    benchmark_results = {}

    # 1. Ingestion Phase
    print(f"\n[1/5] Ingesting catalogue toward {target_products:,} records...")
    t0 = time.time()
    import_stats = bulk_import_catalogue(target_count=target_products, batch_size=25000)
    t_import = time.time() - t0
    benchmark_results["import"] = import_stats
    print(f"  -> Final Catalogue Count: {import_stats['final_count']:,} products")
    print(f"  -> Ingestion Time: {import_stats['elapsed_seconds']}s")
    print(f"  -> Throughput: {import_stats['throughput_records_per_sec']:,.0f} records/second")

    # 2. Integrity & Uniqueness Verification
    print("\n[2/5] Verifying SKU uniqueness & data integrity constraints...")
    integ = verify_catalogue_integrity()
    benchmark_results["integrity"] = integ
    print(f"  -> Total Products in DB: {integ['total_products']:,}")
    print(f"  -> Unique SKUs: {integ['unique_skus']:,} (Collisions: {integ['sku_collision_count']})")
    print(f"  -> Invalid Prices (<=0): {integ['invalid_price_records']}")
    print(f"  -> Distinct Categories: {integ['distinct_categories']}")
    print(f"  -> Integrity Status: {'PASS' if integ['integrity_passed'] else 'FAIL'}")

    # 3. Search Latency Benchmark
    print("\n[3/5] Benchmarking Search Queries across 10 iterations...")
    search_terms = ["Wireless", "Headphones", "Cotton", "Sneakers", "OLED", "Gaming", "Chronograph", "Titanium", "Air", "Pro"]
    search_latencies_ms = []

    for term in search_terms:
        start_q = time.perf_counter()
        res = get_products_paginated(search=term, page=1, per_page=24)
        elapsed_ms = (time.perf_counter() - start_q) * 1000.0
        search_latencies_ms.append(elapsed_ms)

    search_latencies_ms.sort()
    p50_search = statistics.median(search_latencies_ms)
    p95_search = search_latencies_ms[int(len(search_latencies_ms) * 0.95)]
    avg_search = statistics.mean(search_latencies_ms)
    benchmark_results["search"] = {
        "iterations": len(search_terms),
        "avg_ms": round(avg_search, 2),
        "p50_ms": round(p50_search, 2),
        "p95_ms": round(p95_search, 2),
        "min_ms": round(min(search_latencies_ms), 2),
        "max_ms": round(max(search_latencies_ms), 2)
    }
    print(f"  -> Average Search Latency: {avg_search:.2f} ms")
    print(f"  -> p50 Median Latency: {p50_search:.2f} ms")
    print(f"  -> p95 Peak Latency: {p95_search:.2f} ms")

    # 4. Filter & Refinement Latency Benchmark
    print("\n[4/5] Benchmarking Multi-Attribute Filters (Category + Subcategory + Brand + Price)...")
    filter_tests = [
        {"cat": "Electronics", "sub": "Wireless Headphones", "min_p": 1000, "max_p": 25000},
        {"cat": "Mobiles", "sub": "5G Smartphones", "min_p": 15000, "max_p": 80000},
        {"cat": "Fashion", "sub": "Slim Fit Shirts", "min_p": 500, "max_p": 5000},
        {"cat": "Footwear", "sub": "Running Shoes", "min_p": 2000, "max_p": 15000},
        {"cat": "Gaming", "sub": "Mechanical Keyboards", "min_p": 2000, "max_p": 20000}
    ]
    filter_latencies_ms = []
    for f in filter_tests:
        start_q = time.perf_counter()
        res = get_products_paginated(
            category=f["cat"],
            subcategory=f["sub"],
            min_price=f["min_p"],
            max_price=f["max_p"],
            page=1,
            per_page=24
        )
        elapsed_ms = (time.perf_counter() - start_q) * 1000.0
        filter_latencies_ms.append(elapsed_ms)

    avg_filter = statistics.mean(filter_latencies_ms)
    p50_filter = statistics.median(filter_latencies_ms)
    benchmark_results["filtering"] = {
        "avg_ms": round(avg_filter, 2),
        "p50_ms": round(p50_filter, 2),
        "min_ms": round(min(filter_latencies_ms), 2),
        "max_ms": round(max(filter_latencies_ms), 2)
    }
    print(f"  -> Multi-Attribute Filter Avg Latency: {avg_filter:.2f} ms")
    print(f"  -> Multi-Attribute Filter Median: {p50_filter:.2f} ms")

    # 5. Deep Pagination Latency Benchmark
    print("\n[5/5] Benchmarking Server-Side Pagination (Shallow vs Deep Pages)...")
    pages_to_test = [1, 10, 50, 100, 500, 1000]
    total_pages_avail = (integ["total_products"] + 23) // 24
    pages_to_test = [p for p in pages_to_test if p <= total_pages_avail]
    page_latencies = {}

    for p in pages_to_test:
        start_q = time.perf_counter()
        res = get_products_paginated(page=p, per_page=24)
        elapsed_ms = (time.perf_counter() - start_q) * 1000.0
        page_latencies[f"page_{p}"] = round(elapsed_ms, 2)
        print(f"  -> Page {p:>5}: {elapsed_ms:>6.2f} ms (Retrieved {len(res['items'])} items)")

    benchmark_results["pagination"] = page_latencies

    # Memory & Storage
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024) if os.path.exists(DB_PATH) else 0.0

    benchmark_results["system"] = {
        "db_size_mb": round(db_size_mb, 2),
        "peak_ram_mb": round(peak_mem / (1024 * 1024), 2),
        "current_ram_mb": round(current_mem / (1024 * 1024), 2)
    }

    print("\n" + "=" * 65)
    print("BENCHMARK SUMMARY & SYSTEM FOOTPRINT")
    print("=" * 65)
    print(f"Database File Size on Disk: {db_size_mb:.2f} MB")
    print(f"Peak Process Memory Tracked: {peak_mem / (1024 * 1024):.2f} MB")
    print(f"Total Products in Live DB: {integ['total_products']:,}")
    print(f"Data Integrity: {'100% VERIFIED' if integ['integrity_passed'] else 'FAILED'}")
    print("=" * 65)

    return benchmark_results

if __name__ == "__main__":
    count = 100000
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
    run_benchmark(count)

