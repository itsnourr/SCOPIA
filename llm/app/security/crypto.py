"""
AES-256-CBC Encryption/Decryption for Evidence Files

Provides secure at-rest storage for images and binary files using:
- AES-256-CBC encryption
- Random 16-byte IVs
- PKCS#7 padding
- SHA-256 integrity checksums

Example Usage:
    >>> from app.security.crypto import encrypt_bytes, decrypt_bytes
    >>> from config import Config
    >>> 
    >>> # Encrypt data
    >>> data = b"Secret Evidence"
    >>> iv_hex, ciphertext, sha256_hex = encrypt_bytes(data, Config.AES_MASTER_KEY)
    >>> 
    >>> # Decrypt data
    >>> plaintext = decrypt_bytes(ciphertext, Config.AES_MASTER_KEY, iv_hex)
    >>> assert plaintext == data
    >>> 
    >>> # Save encrypted file
    >>> metadata = save_encrypted_file("evidence.jpg", image_bytes, Config.AES_MASTER_KEY)
    >>> # Returns: {"file_path": "...", "iv_hex": "...", "sha256_hex": "..."}
    >>> 
    >>> # Load and decrypt file
    >>> decrypted = decrypt_file_to_bytes(
    ...     metadata["file_path"],
    ...     Config.AES_MASTER_KEY,
    ...     metadata["iv_hex"]
    ... )
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Dict
from uuid import uuid4

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from config import Config


logger = logging.getLogger(__name__)


AES_BLOCK_SIZE = 16
AES_KEY_SIZE = 32
IV_SIZE = 16


class CryptoError(Exception):
    """Base exception for cryptography errors"""
    pass


class InvalidKeyError(CryptoError):
    """Raised when encryption key is invalid"""
    pass


class DecryptionError(CryptoError):
    """Raised when decryption fails"""
    pass


class IntegrityError(CryptoError):
    """Raised when data integrity check fails"""
    pass


def _validate_key(key_hex: str) -> bytes:
    """
    Validate and convert hex key to bytes
    
    Args:
        key_hex: Hexadecimal key string (64 chars for 32 bytes)
        
    Returns:
        Key as bytes
        
    Raises:
        InvalidKeyError: If key format is invalid
    """
    if not key_hex:
        raise InvalidKeyError("Encryption key is empty")
    
    if len(key_hex) != 64:
        raise InvalidKeyError(
            f"Invalid key length: expected 64 hex chars (32 bytes), got {len(key_hex)}"
        )
    
    try:
        key_bytes = bytes.fromhex(key_hex)
    except ValueError as e:
        raise InvalidKeyError(f"Invalid hex string in key: {e}")
    
    if len(key_bytes) != AES_KEY_SIZE:
        raise InvalidKeyError(
            f"Key must be {AES_KEY_SIZE} bytes for AES-256, got {len(key_bytes)}"
        )
    
    return key_bytes


def _compute_sha256(data: bytes) -> str:
    """
    Compute SHA-256 hash of data
    
    Args:
        data: Bytes to hash
        
    Returns:
        Hexadecimal hash string (64 chars)
    """
    return hashlib.sha256(data).hexdigest()


def _generate_iv() -> bytes:
    """
    Generate cryptographically secure random IV
    
    Returns:
        16-byte random IV
    """
    return os.urandom(IV_SIZE)


def encrypt_bytes(data: bytes, key_hex: str) -> Tuple[str, bytes, str]:
    """
    Encrypt bytes using AES-256-CBC with PKCS#7 padding
    
    Args:
        data: Plaintext data to encrypt
        key_hex: 64-character hexadecimal key string (32 bytes)
        
    Returns:
        Tuple of (iv_hex, ciphertext_bytes, sha256_hex):
            - iv_hex: Initialization vector as hex string (32 chars)
            - ciphertext_bytes: Encrypted data
            - sha256_hex: SHA-256 hash of original plaintext (64 chars)
            
    Raises:
        InvalidKeyError: If key is invalid
        CryptoError: If encryption fails
        
    Example:
        >>> data = b"Sensitive evidence data"
        >>> iv_hex, ciphertext, sha256_hex = encrypt_bytes(data, "a" * 64)
        >>> len(iv_hex)
        32
        >>> isinstance(ciphertext, bytes)
        True
    """

    if data is None:
        raise TypeError("data cannot be None")
    if not isinstance(data, bytes):
        raise TypeError(f"data must be bytes, got {type(data).__name__}")
    if not isinstance(key_hex, str):
        raise TypeError(f"key_hex must be str, got {type(key_hex).__name__}")
    
    try:

        key_bytes = _validate_key(key_hex)
        

        iv = _generate_iv()
        

        sha256_hex = _compute_sha256(data)
        

        padded_data = pad(data, AES_BLOCK_SIZE)
        

        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(padded_data)
        

        iv_hex = iv.hex()
        
        logger.debug(
            f"Encrypted {len(data)} bytes → {len(ciphertext)} bytes "
            f"(IV: {iv_hex[:8]}..., SHA-256: {sha256_hex[:8]}...)"
        )
        
        return iv_hex, ciphertext, sha256_hex
        
    except InvalidKeyError:
        raise
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise CryptoError(f"Encryption failed: {e}")


def decrypt_bytes(
    ciphertext: bytes,
    key_hex: str,
    iv_hex: str,
    verify_sha256: str = None
) -> bytes:
    """
    Decrypt bytes using AES-256-CBC with PKCS#7 unpadding
    
    Args:
        ciphertext: Encrypted data
        key_hex: 64-character hexadecimal key string (32 bytes)
        iv_hex: 32-character hexadecimal IV string (16 bytes)
        verify_sha256: Optional SHA-256 hash to verify decrypted data integrity
        
    Returns:
        Decrypted plaintext bytes
        
    Raises:
        InvalidKeyError: If key or IV is invalid
        DecryptionError: If decryption fails (wrong key/IV)
        IntegrityError: If SHA-256 verification fails
        
    Example:
        >>> key = "a" * 64
        >>> iv_hex, ciphertext, sha256 = encrypt_bytes(b"Test", key)
        >>> plaintext = decrypt_bytes(ciphertext, key, iv_hex, sha256)
        >>> plaintext
        b'Test'
    """

    if ciphertext is None:
        raise TypeError("ciphertext cannot be None")
    if not isinstance(ciphertext, bytes):
        raise TypeError(f"ciphertext must be bytes, got {type(ciphertext).__name__}")
    if not isinstance(key_hex, str):
        raise TypeError(f"key_hex must be str, got {type(key_hex).__name__}")
    if not isinstance(iv_hex, str):
        raise TypeError(f"iv_hex must be str, got {type(iv_hex).__name__}")
    
    try:

        key_bytes = _validate_key(key_hex)
        

        if not iv_hex:
            raise InvalidKeyError("IV is empty")
        
        if len(iv_hex) != 32:
            raise InvalidKeyError(
                f"Invalid IV length: expected 32 hex chars (16 bytes), got {len(iv_hex)}"
            )
        
        try:
            iv = bytes.fromhex(iv_hex)
        except ValueError as e:
            raise InvalidKeyError(f"Invalid hex string in IV: {e}")
        

        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        
        try:
            padded_plaintext = cipher.decrypt(ciphertext)
            plaintext = unpad(padded_plaintext, AES_BLOCK_SIZE)
        except ValueError as e:

            raise DecryptionError(
                f"Decryption failed - incorrect key or IV: {e}"
            )
        

        if verify_sha256:
            computed_sha256 = _compute_sha256(plaintext)
            if computed_sha256 != verify_sha256:
                raise IntegrityError(
                    f"Data integrity check failed: "
                    f"expected {verify_sha256}, got {computed_sha256}"
                )
            logger.debug("✅ Data integrity verified (SHA-256 match)")
        
        logger.debug(
            f"Decrypted {len(ciphertext)} bytes → {len(plaintext)} bytes"
        )
        
        return plaintext
        
    except (InvalidKeyError, DecryptionError, IntegrityError):
        raise
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise DecryptionError(f"Decryption failed: {e}")


def save_encrypted_file(
    filename: str,
    data: bytes,
    key_hex: str,
    output_dir: str = None
) -> Dict[str, str]:
    """
    Encrypt data and save to disk with unique filename
    
    Args:
        filename: Original filename (for reference, not used as actual filename)
        data: Plaintext data to encrypt and save
        key_hex: 64-character hexadecimal key string (32 bytes)
        output_dir: Directory to save encrypted file (default: Config.FILES_DIR)
        
    Returns:
        Dictionary with metadata:
            - file_path: Path to encrypted file
            - iv_hex: Initialization vector (hex)
            - sha256_hex: SHA-256 hash of plaintext
            - original_filename: Original filename
            - size_bytes: Size of encrypted file
            
    Raises:
        InvalidKeyError: If key is invalid
        CryptoError: If encryption or file I/O fails
        
    Example:
        >>> data = b"Evidence photo data..."
        >>> metadata = save_encrypted_file("evidence.jpg", data, "a" * 64)
        >>> metadata.keys()
        dict_keys(['file_path', 'iv_hex', 'sha256_hex', 'original_filename', 'size_bytes'])
    """
    try:

        if output_dir is None:
            output_dir = Config.FILES_DIR
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        

        iv_hex, ciphertext, sha256_hex = encrypt_bytes(data, key_hex)
        

        unique_id = uuid4().hex
        file_extension = Path(filename).suffix or ".enc"
        encrypted_filename = f"{unique_id}{file_extension}.enc"
        file_path = output_path / encrypted_filename
        

        with open(file_path, "wb") as f:
            f.write(ciphertext)
        
        metadata = {
            "file_path": str(file_path),
            "iv_hex": iv_hex,
            "sha256_hex": sha256_hex,
            "original_filename": filename,
            "size_bytes": len(ciphertext)
        }
        
        logger.info(
            f"✅ Saved encrypted file: {encrypted_filename} "
            f"({len(data)} bytes → {len(ciphertext)} bytes)"
        )
        
        return metadata
        
    except InvalidKeyError:
        raise
    except CryptoError:
        raise
    except Exception as e:
        logger.error(f"Failed to save encrypted file: {e}")
        raise CryptoError(f"Failed to save encrypted file: {e}")


def decrypt_file_to_bytes(
    file_path: str,
    key_hex: str,
    iv_hex: str,
    verify_sha256: str = None
) -> bytes:
    """
    Read encrypted file from disk and decrypt to bytes
    
    Args:
        file_path: Path to encrypted file
        key_hex: 64-character hexadecimal key string (32 bytes)
        iv_hex: 32-character hexadecimal IV string (16 bytes)
        verify_sha256: Optional SHA-256 hash to verify data integrity
        
    Returns:
        Decrypted plaintext bytes
        
    Raises:
        FileNotFoundError: If file does not exist
        InvalidKeyError: If key or IV is invalid
        DecryptionError: If decryption fails
        IntegrityError: If SHA-256 verification fails
        
    Example:
        >>> # After saving encrypted file
        >>> metadata = save_encrypted_file("test.txt", b"Secret", "a" * 64)
        >>> decrypted = decrypt_file_to_bytes(
        ...     metadata["file_path"],
        ...     "a" * 64,
        ...     metadata["iv_hex"],
        ...     metadata["sha256_hex"]
        ... )
        >>> decrypted
        b'Secret'
    """
    try:

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Encrypted file not found: {file_path}")
        
        with open(path, "rb") as f:
            ciphertext = f.read()
        
        logger.debug(f"Read encrypted file: {path.name} ({len(ciphertext)} bytes)")
        

        plaintext = decrypt_bytes(ciphertext, key_hex, iv_hex, verify_sha256)
        
        logger.info(f"✅ Decrypted file: {path.name} ({len(plaintext)} bytes)")
        
        return plaintext
        
    except (FileNotFoundError, InvalidKeyError, DecryptionError, IntegrityError):
        raise
    except Exception as e:
        logger.error(f"Failed to decrypt file: {e}")
        raise CryptoError(f"Failed to decrypt file: {e}")


def delete_encrypted_file(file_path: str) -> bool:
    """
    Securely delete an encrypted file
    
    Args:
        file_path: Path to encrypted file
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.info(f"✅ Deleted encrypted file: {path.name}")
            return True
        else:
            logger.warning(f"File not found for deletion: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Failed to delete encrypted file: {e}")
        return False



if __name__ == "__main__":
    """
    Quick test of encryption/decryption functionality
    
    Run with: python -m app.security.crypto
    """
    print("=" * 60)
    print("AES-256-CBC Encryption Test")
    print("=" * 60)
    

    if not Config.AES_MASTER_KEY or len(Config.AES_MASTER_KEY) != 64:
        print("❌ AES_MASTER_KEY not configured properly in .env")
        print("Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")
        exit(1)
    

    test_data = b"Secret Evidence: Fingerprint found at crime scene"
    print(f"\n📝 Original data: {test_data}")
    print(f"📏 Size: {len(test_data)} bytes")
    

    print("\n🔒 Encrypting...")
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(test_data, Config.AES_MASTER_KEY)
    print(f"✅ IV: {iv_hex}")
    print(f"✅ SHA-256: {sha256_hex}")
    print(f"✅ Ciphertext size: {len(ciphertext)} bytes")
    

    print("\n🔓 Decrypting...")
    plaintext = decrypt_bytes(ciphertext, Config.AES_MASTER_KEY, iv_hex, sha256_hex)
    print(f"✅ Decrypted: {plaintext}")
    

    if plaintext == test_data:
        print("\n✅ Round-trip encryption/decryption successful!")
    else:
        print("\n❌ Round-trip verification failed!")
    

    print("\n📁 Testing file operations...")
    metadata = save_encrypted_file("test_evidence.txt", test_data, Config.AES_MASTER_KEY)
    print(f"✅ Saved to: {metadata['file_path']}")
    
    decrypted_from_file = decrypt_file_to_bytes(
        metadata["file_path"],
        Config.AES_MASTER_KEY,
        metadata["iv_hex"],
        metadata["sha256_hex"]
    )
    
    if decrypted_from_file == test_data:
        print("✅ File encryption/decryption successful!")
    else:
        print("❌ File verification failed!")
    

    delete_encrypted_file(metadata["file_path"])
    print("\n✅ Test complete!")

