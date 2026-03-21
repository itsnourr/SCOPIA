## 🔐 Security Module

Encryption and security utilities for the Forensic Crime Analysis Agent.

---

## 📦 Available Implementations

### ✅ **RECOMMENDED: `crypto_adapted.py`**

Python adaptation of the user's proven Java InfoSec encryption system.

**Features:**
- ✅ AES-256-CBC encryption
- ✅ HMAC-SHA256 integrity verification
- ✅ Random IV prepended to encrypted file
- ✅ Key caching for performance
- ✅ Constant-time HMAC comparison
- ✅ Matches user's existing Java system

**Architecture:**
```
Encrypted File Format:
┌────────────┬──────────────────┐
│ IV (16 B)  │ Ciphertext       │
└────────────┴──────────────────┘
```

**Database Storage:**
- `file_path`: Path to encrypted file
- `iv_base64`: IV in Base64 (also in file, but stored for reference)
- `hmac_base64`: HMAC-SHA256 for integrity verification

---

###  **Alternative: `crypto.py`**

Original implementation with separate IV storage.

**Features:**
- ✅ AES-256-CBC encryption
- ✅ SHA-256 checksum
- ✅ IV returned separately (not prepended)
- ✅ Useful for database-first workflows

**Use when:**
- You prefer storing IV separately in database
- Don't need HMAC (SHA-256 sufficient)

---

## 🚀 Quick Start

### Using CryptoService (Recommended)

```python
from app.security import CryptoService

# Initialize service
crypto = CryptoService()

# Encrypt a file
metadata = crypto.encrypt_file(
    filename="evidence.jpg",
    data=image_bytes
)
# Returns: {
#   "file_path": "/data/encrypted/abc123.jpg.enc",
#   "iv_base64": "dGVzdA==",
#   "hmac_base64": "aG1hYw==",
#   "original_filename": "evidence.jpg",
#   "size_bytes": 1234
# }

# Decrypt with integrity check
decrypted = crypto.decrypt_file(
    metadata["file_path"],
    stored_hmac_base64=metadata["hmac_base64"]
)

# Verify HMAC before decryption
encrypted_bytes = crypto.read_encrypted_file(metadata["file_path"])
is_valid = crypto.verify_hmac(encrypted_bytes, metadata["hmac_base64"])
```

### Using Singleton Instance

```python
from app.security import get_crypto_service

crypto = get_crypto_service()  # Returns cached instance
metadata = crypto.encrypt_file("photo.jpg", photo_bytes)
```

### Low-Level API (Backwards Compatible)

```python
from app.security import encrypt_bytes, decrypt_bytes

# Encrypt
iv_hex, ciphertext, sha256_hex = encrypt_bytes(data, key_hex)

# Decrypt
plaintext = decrypt_bytes(ciphertext, key_hex, iv_hex, sha256_hex)
```

---

## 🗃️ Database Integration

### Database Schema (Image table)

```python
class Image(Base):
    file_path: str      # Path to encrypted file (IV prepended)
    iv_hex: str         # IV as hex (also in file, but stored for reference)
    sha256_hex: str     # SHA-256 of plaintext (for verification)
    hmac_base64: str    # HMAC-SHA256 for integrity (RECOMMENDED)
```

### Upload Workflow

```python
from app.security import get_crypto_service
from app.db import add_image

crypto = get_crypto_service()

# 1. Encrypt and save file
metadata = crypto.encrypt_file("evidence.jpg", image_bytes)

# 2. Store metadata in database
image = add_image(
    case_id=case_id,
    filename="evidence.jpg",
    file_path=metadata["file_path"],
    iv_hex=base64.b64decode(metadata["iv_base64"]).hex(),
    sha256_hex=hashlib.sha256(image_bytes).hexdigest()
)

# 3. Optionally store HMAC (recommended)
# Store metadata["hmac_base64"] in a separate field or JSON column
```

### Download Workflow

```python
from app.security import get_crypto_service
from app.db import get_images_by_case

crypto = get_crypto_service()

# 1. Get image metadata from database
images = get_images_by_case(case_id)
image = images[0]

# 2. Decrypt with HMAC verification
try:
    decrypted = crypto.decrypt_file(
        image.file_path,
        stored_hmac_base64=stored_hmac  # From DB or JSON metadata
    )
except ValueError as e:
    print(f"❌ Integrity check failed: {e}")
```

---

## 🔑 Key Management

### Configuration (.env)

```bash
# 32-byte hex key (64 characters)
AES_MASTER_KEY=your_64_character_hex_key_here
```

### Generate Key

```bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"

# PowerShell
$key = -join ((48..57) + (97..102) | Get-Random -Count 64 | % {[char]$_})
Write-Output $key
```

### Key Security

✅ **DO:**
- Store key in `.env` (excluded from Git)
- Use 32 bytes (64 hex chars) for AES-256
- Backup key securely (losing it = losing all data)
- Use different keys for dev/staging/production

❌ **DON'T:**
- Commit keys to Git
- Share keys in plain text
- Reuse keys across projects
- Use weak/short keys

---

## 🧪 Testing

```bash
# Test adapted version
python -m app.security.crypto_adapted

# Run unit tests
pytest app/tests/test_crypto.py -v

# Test with coverage
pytest app/tests/test_crypto.py --cov=app.security
```

---

## 🔒 Security Properties

### Encryption (AES-256-CBC)

- ✅ **Confidentiality**: AES-256 is industry standard
- ✅ **Random IV**: Each encryption uses unique IV
- ✅ **PKCS#7 Padding**: Proper block alignment
- ✅ **CBC Mode**: Chaining prevents pattern analysis

### Integrity (HMAC-SHA256)

- ✅ **Tamper Detection**: HMAC detects any modifications
- ✅ **Constant-Time Comparison**: Prevents timing attacks
- ✅ **Authenticate-Then-Encrypt**: HMAC covers IV + ciphertext

### Key Management

- ✅ **Key Caching**: Loaded once, cached for performance
- ✅ **Separation**: Encryption key separate from HMAC key
- ✅ **Secure Storage**: Keys outside version control

---

## 📊 Comparison: crypto.py vs crypto_adapted.py

| Feature | crypto.py | crypto_adapted.py |
|---------|-----------|-------------------|
| AES-256-CBC | ✅ | ✅ |
| Random IV | ✅ | ✅ |
| IV Storage | Separate (database) | Prepended to file |
| Integrity Check | SHA-256 checksum | HMAC-SHA256 |
| Key Caching | ❌ | ✅ |
| Performance | Good | Better (cached keys) |
| Security Level | High | Higher (HMAC) |
| Matches Java System | ❌ | ✅ |
| **Recommended** | For DB-first | **YES** ✅ |

---

## ⚠️ Important Notes

1. **IV Prepending**: The adapted version prepends IV to encrypted files (matches Java system)
2. **HMAC Verification**: Always verify HMAC BEFORE decryption
3. **Key Backup**: Losing encryption key = losing all encrypted data
4. **Database Fields**: Need to store `hmac_base64` for integrity verification
5. **File Format**: Encrypted files are NOT plain AES output - they include IV

---

## 🔄 Migration from Original

If you started with `crypto.py` and want to migrate:

1. **Database**: Add `hmac_base64` column to `images` table
2. **Files**: Re-encrypt files with adapted version
3. **Code**: Update imports to use `crypto_adapted`
4. **Testing**: Verify HMAC on all decrypt operations

---

## 📝 Next Steps

After setting up encryption:
1. **Integrate with database**: Update `add_image()` to store HMAC
2. **Streamlit upload**: Use `crypto.encrypt_file()` in file upload handler
3. **Image Analyzer tool**: Use `crypto.decrypt_file()` to read images
4. **Testing**: Add integration tests with real images

---

## 🆘 Troubleshooting

### "Key must be 64 hex chars"
- Check `.env` has `AES_MASTER_KEY=<64_chars>`
- Generate new key: `python -c "import secrets; print(secrets.token_hex(32))"`

### "HMAC verification failed"
- File may have been tampered with
- Check HMAC was stored correctly
- Verify same key is being used

### "Invalid padding"
- Wrong encryption key
- Corrupted file
- Wrong IV

### "File integrity check failed"
- File modified after encryption
- HMAC key mismatch
- Corrupted storage

---

✅ **Ready to use!** The adapted crypto system matches your proven Java implementation.

