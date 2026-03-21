"""
Security utilities: encryption, validation, ethical guardrails

Two encryption implementations available:

1. **crypto.py** (Original) - Separate IV storage
   - Returns IV separately for database storage
   - SHA-256 for integrity
   - Best for: Database-first approach

2. **crypto_adapted.py** (Java-adapted) - IV prepended to file
   - IV prepended to encrypted file (like Java InfoSec project)
   - HMAC-SHA256 for integrity
   - Key caching for performance
   - Best for: File-based storage, matches user's existing system

**Recommended:** Use crypto_adapted.py (matches your proven Java system)
"""


from app.security.crypto_adapted import (
    CryptoService,
    get_crypto_service,
    encrypt_bytes,
    decrypt_bytes,
)

__all__ = [
    "CryptoService",
    "get_crypto_service",
    "encrypt_bytes",
    "decrypt_bytes",
]
