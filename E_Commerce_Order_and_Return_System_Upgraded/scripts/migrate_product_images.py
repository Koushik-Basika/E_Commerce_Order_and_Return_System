"""
Standalone image migration runner command for VS Code.
Usage:
    python scripts/migrate_product_images.py            # Run migration with auto-backup
    python scripts/migrate_product_images.py --rollback # Rollback to previous backup
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.migrate_images import migrate_product_images, rollback_db_backup

def main():
    if "--rollback" in sys.argv:
        print("[*] Initiating database rollback from backup...")
        success = rollback_db_backup()
        sys.exit(0 if success else 1)
    else:
        print("[*] Initiating database product image migration...")
        res = migrate_product_images()
        if res.get("status") == "success" and res["post_kpis"]["unique_images"] >= 300:
            print("[SUCCESS] Product image migration completed successfully with 300+ unique verified images!")
            sys.exit(0)
        else:
            print("[FAIL] Product image migration failed.")
            sys.exit(1)

if __name__ == "__main__":
    main()
