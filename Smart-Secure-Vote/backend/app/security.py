import hashlib, hmac, secrets
from .config import JWT_SECRET

def hash_otp(code: str) -> str:
    return hmac.new(JWT_SECRET.encode(), code.encode(), hashlib.sha256).hexdigest()

def verify_otp(code: str, digest: str) -> bool:
    return hmac.compare_digest(hash_otp(code), digest)

def new_receipt() -> str:
    return secrets.token_hex(8).upper()
