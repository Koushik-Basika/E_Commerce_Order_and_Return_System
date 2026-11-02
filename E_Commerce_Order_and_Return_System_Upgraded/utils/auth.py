import hashlib
import secrets

def hash_password(password: str, salt: str = None) -> str:
    """Hashes a password with PBKDF2-HMAC-SHA256 and a 16-byte random salt."""
    if not password:
        return ""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return f"{salt}${digest}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a password against a stored salt$digest string."""
    if not password or not stored_hash:
        return False
    try:
        if "$" not in stored_hash:
            return False
        salt, digest = stored_hash.split("$", 1)
        calc_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
        return secrets.compare_digest(calc_digest, digest)
    except Exception:
        return False
