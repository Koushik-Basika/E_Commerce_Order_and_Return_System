"""
Standalone image validation runner command for VS Code.
Usage:
    python scripts/validate_images.py
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from utils.image_validator import validate_catalog_file, print_validation_report

def main():
    print("[*] Initiating comprehensive product image validation scan...")
    report = validate_catalog_file()
    print_validation_report(report)
    if report.get("is_sufficient"):
        print("[SUCCESS] Image catalog meets and exceeds all portfolio standards!")
        sys.exit(0)
    else:
        print("[FAIL] Image catalog did not meet the 300+ unique verified threshold.")
        sys.exit(1)

if __name__ == "__main__":
    main()
