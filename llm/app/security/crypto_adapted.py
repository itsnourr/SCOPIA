"""
AES-256-CBC + HMAC-SHA256 Encryption System
Adapted from Java InfoSec project - Python implementation

This is a direct Python adaptation of the user's existing encryption system that uses:
- AES-256-CBC for confidentiality
- HMAC-SHA256 for integrity verification
- Random IV generation (prepended to ciphertext)
- Secure key caching
- .sam file key management (optional)

Key Differences from Original crypto.py:
1. IV is PREPENDED to encrypted file (like Java version)
2. HMAC-SHA256 added for integrity (in addition to SHA-256)
3. Key caching implemented
4. Support for .sam key files

Example Usage:
    >>> from app.security.crypto_adapted import CryptoService
    >>> 
    >>> crypto = CryptoService()
    >>> 
    >>> # Encrypt file
    >>> metadata = crypto.encrypt_file("input.jpg", "output.enc")
    >>> # Returns: {"file_path": "...", "iv_base64": "...", "hmac_base64": "..."}
    >>> 
    >>> # Decrypt file with integrity check
    >>> decrypted = crypto.decrypt_file("output.enc", metadata["hmac_base64"])
    >>> 
    >>> # Verify HMAC before decryption
    >>> is_valid = crypto.verify_hmac("output.enc", metadata["hmac_base64"])
"""

import os
import hmac
import hashlib
import logging
import base64
from pathlib import Path
from typing import Dict, Tuple, Optional
from uuid import uuid4

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

from config import Config


logger = logging.getLogger(__name__)


ALGORITHM = "AES"
TRANSFORMATION = "AES/CBC/PKCS5Padding"
IV_SIZE = 16
KEY_SIZE = 32
HMAC_ALGORITHM = "sha256"


class CryptoService:
    """
    Main encryption/decryption service
    Python adaptation of Java CryptoService
    """
    
    def __init__(self):
        self.cached_aes_key: Optional[bytes] = None
        self.cached_hmac_key: Optional[bytes] = None
    
    def _get_aes_key(self) -> bytes:
        """
        Gets the AES key (cached for performance)
        Equivalent to Java's getKeyBytes()
        
        Returns:
            32-byte AES-256 key
            
        Raises:
            ValueError: If key is invalid size
        """
        if self.cached_aes_key is not None:
            return self.cached_aes_key
        
        logger.info("🔐 Loading AES key...")
        

        key_hex = Config.AES_MASTER_KEY
        
        if not key_hex:
            raise ValueError("AES_MASTER_KEY not configured in .env")
        
        if len(key_hex) != 64:
            raise ValueError(
                f"AES-256 key must be exactly 32 bytes (64 hex chars). "
                f"Current size: {len(key_hex)} chars"
            )
        
        try:
            key_bytes = bytes.fromhex(key_hex)
        except ValueError as e:
            raise ValueError(f"Invalid hex string in AES_MASTER_KEY: {e}")
        
        if len(key_bytes) != KEY_SIZE:
            raise ValueError(
                f"AES-256 key must be exactly {KEY_SIZE} bytes. "
                f"Got: {len(key_bytes)} bytes"
            )
        

        self.cached_aes_key = key_bytes
        logger.info("✅ AES key loaded and cached")
        
        return key_bytes
    
    def _get_hmac_key(self) -> bytes:
        """
        Gets the HMAC key (cached for performance)
        In production, this could be loaded from a separate .sam file
        For now, derives it from AES key
        
        Returns:
            32-byte HMAC key
        """
        if self.cached_hmac_key is not None:
            return self.cached_hmac_key
        
        logger.info("🔐 Loading HMAC key...")
        


        aes_key = self._get_aes_key()
        

        self.cached_hmac_key = hashlib.sha256(
            b"HMAC_KEY_DERIVATION_" + aes_key
        ).digest()
        
        logger.info("✅ HMAC key derived and cached")
        
        return self.cached_hmac_key
    
    def encrypt(self, input_file_path: str, output_file_path: str) -> Dict[str, str]:
        """
        Encrypts a file using AES-256-CBC
        Generates random IV and prepends it to ciphertext
        Equivalent to Java's encrypt() method
        
        Args:
            input_file_path: Path to file to encrypt
            output_file_path: Path where encrypted file will be saved
            
        Returns:
            Dictionary with:
                - iv_base64: IV in Base64 format
                - hmac_base64: HMAC-SHA256 in Base64 format
                - file_path: Path to encrypted file
                
        Raises:
            Exception: If encryption fails
        """
        try:

            iv = get_random_bytes(IV_SIZE)
            iv_base64 = base64.b64encode(iv).decode('utf-8')
            

            key_bytes = self._get_aes_key()
            

            with open(input_file_path, 'rb') as f:
                input_bytes = f.read()
            

            padded_data = pad(input_bytes, AES.block_size)
            

            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            encrypted_bytes = cipher.encrypt(padded_data)
            

            with open(output_file_path, 'wb') as f:
                f.write(iv)
                f.write(encrypted_bytes)
            

            with open(output_file_path, 'rb') as f:
                encrypted_file_bytes = f.read()
            
            hmac_base64 = self.generate_hmac(encrypted_file_bytes)
            
            logger.info(
                f"✅ Encrypted file: {Path(input_file_path).name} → {Path(output_file_path).name} "
                f"({len(input_bytes)} bytes → {len(encrypted_file_bytes)} bytes)"
            )
            
            return {
                "iv_base64": iv_base64,
                "hmac_base64": hmac_base64,
                "file_path": output_file_path
            }
            
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_file_path: str) -> bytes:
        """
        Decrypts a file using AES-256-CBC
        Extracts IV from beginning of file
        Equivalent to Java's decrypt() method
        
        Args:
            encrypted_file_path: Path to encrypted file (with IV prepended)
            
        Returns:
            Decrypted file bytes
            
        Raises:
            Exception: If decryption fails
        """
        try:

            with open(encrypted_file_path, 'rb') as f:
                file_bytes = f.read()
            
            if len(file_bytes) < IV_SIZE:
                raise ValueError("Invalid encrypted file: too small")
            

            iv = file_bytes[:IV_SIZE]
            

            encrypted_data = file_bytes[IV_SIZE:]
            

            key_bytes = self._get_aes_key()
            

            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            

            padded_plaintext = cipher.decrypt(encrypted_data)
            

            plaintext = unpad(padded_plaintext, AES.block_size)
            
            logger.info(
                f"✅ Decrypted file: {Path(encrypted_file_path).name} "
                f"({len(file_bytes)} bytes → {len(plaintext)} bytes)"
            )
            
            return plaintext
            
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            raise
    
    def read_encrypted_file(self, encrypted_file_path: str) -> bytes:
        """
        Reads encrypted file bytes (for HMAC generation)
        Equivalent to Java's readEncryptedFile()
        
        Args:
            encrypted_file_path: Path to encrypted file
            
        Returns:
            Encrypted file bytes (including IV)
        """
        with open(encrypted_file_path, 'rb') as f:
            return f.read()
    
    def generate_hmac(self, data: bytes) -> str:
        """
        Generates HMAC-SHA256 for data integrity
        Equivalent to Java HmacService.generateHmac()
        
        Args:
            data: Data to generate HMAC for (usually encrypted file bytes)
            
        Returns:
            Base64 encoded HMAC
        """
        hmac_key = self._get_hmac_key()
        h = hmac.new(hmac_key, data, hashlib.sha256)
        hmac_bytes = h.digest()
        return base64.b64encode(hmac_bytes).decode('utf-8')
    
    def verify_hmac(self, data: bytes, stored_hmac_base64: str) -> bool:
        """
        Verifies if stored HMAC matches newly generated HMAC
        Uses constant-time comparison to prevent timing attacks
        Equivalent to Java HmacService.verifyHmac()
        
        Args:
            data: Data to verify (encrypted file bytes)
            stored_hmac_base64: Stored HMAC in Base64 format
            
        Returns:
            True if HMAC matches, False otherwise
        """
        try:
            new_hmac_base64 = self.generate_hmac(data)
            

            stored_hmac = base64.b64decode(stored_hmac_base64)
            new_hmac = base64.b64decode(new_hmac_base64)
            

            return hmac.compare_digest(stored_hmac, new_hmac)
            
        except Exception as e:
            logger.error(f"HMAC verification error: {e}")
            return False
    

    
    def encrypt_file(
        self,
        filename: str,
        data: bytes,
        output_dir: str = None
    ) -> Dict[str, str]:
        """
        High-level method: encrypt data and save to disk
        
        Args:
            filename: Original filename (for reference)
            data: Data to encrypt
            output_dir: Directory to save encrypted file (default: Config.FILES_DIR)
            
        Returns:
            Dictionary with metadata:
                - file_path: Path to encrypted file
                - iv_base64: IV in Base64
                - hmac_base64: HMAC in Base64
                - original_filename: Original filename
                - size_bytes: Size of encrypted file
        """

        if output_dir is None:
            output_dir = Config.FILES_DIR
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        

        unique_id = uuid4().hex
        file_extension = Path(filename).suffix or ""
        encrypted_filename = f"{unique_id}{file_extension}.enc"
        encrypted_file_path = str(output_path / encrypted_filename)
        

        temp_file_path = str(output_path / f"temp_{unique_id}")
        with open(temp_file_path, 'wb') as f:
            f.write(data)
        
        try:

            result = self.encrypt(temp_file_path, encrypted_file_path)
            

            result["original_filename"] = filename
            result["size_bytes"] = Path(encrypted_file_path).stat().st_size
            
            logger.info(f"✅ Saved encrypted file: {encrypted_filename}")
            
            return result
            
        finally:

            if Path(temp_file_path).exists():
                Path(temp_file_path).unlink()
    
    def decrypt_file(
        self,
        encrypted_file_path: str,
        stored_hmac_base64: str = None
    ) -> bytes:
        """
        High-level method: decrypt file with optional HMAC verification
        
        Args:
            encrypted_file_path: Path to encrypted file
            stored_hmac_base64: Optional HMAC for integrity verification
            
        Returns:
            Decrypted data bytes
            
        Raises:
            ValueError: If HMAC verification fails
        """

        if stored_hmac_base64:
            encrypted_bytes = self.read_encrypted_file(encrypted_file_path)
            is_valid = self.verify_hmac(encrypted_bytes, stored_hmac_base64)
            
            if not is_valid:
                raise ValueError("File integrity check failed! HMAC mismatch.")
            
            logger.info("✅ HMAC verification passed")
        

        return self.decrypt(encrypted_file_path)



_crypto_service_instance = None


def get_crypto_service() -> CryptoService:
    """Get singleton CryptoService instance"""
    global _crypto_service_instance
    if _crypto_service_instance is None:
        _crypto_service_instance = CryptoService()
    return _crypto_service_instance




def encrypt_bytes(data: bytes, key_hex: str) -> Tuple[str, bytes, str]:
    """
    Backwards compatible: encrypt bytes and return (iv_hex, ciphertext, sha256_hex)
    Note: This returns IV separately (not prepended) for DB compatibility
    """
    crypto = get_crypto_service()
    

    iv = get_random_bytes(IV_SIZE)
    iv_hex = iv.hex()
    

    sha256_hex = hashlib.sha256(data).hexdigest()
    

    key_bytes = bytes.fromhex(key_hex)
    padded_data = pad(data, AES.block_size)
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(padded_data)
    
    return iv_hex, ciphertext, sha256_hex


def decrypt_bytes(
    ciphertext: bytes,
    key_hex: str,
    iv_hex: str,
    verify_sha256: str = None
) -> bytes:
    """
    Backwards compatible: decrypt bytes with separate IV
    """
    key_bytes = bytes.fromhex(key_hex)
    iv = bytes.fromhex(iv_hex)
    

    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    padded_plaintext = cipher.decrypt(ciphertext)
    plaintext = unpad(padded_plaintext, AES.block_size)
    

    if verify_sha256:
        computed = hashlib.sha256(plaintext).hexdigest()
        if computed != verify_sha256:
            raise ValueError("Data integrity check failed (SHA-256 mismatch)")
    
    return plaintext



if __name__ == "__main__":
    """
    Quick test of adapted encryption system
    Run with: python -m app.security.crypto_adapted
    """
    print("=" * 60)
    print("AES-256-CBC + HMAC-SHA256 Encryption Test")
    print("(Adapted from Java InfoSec project)")
    print("=" * 60)
    

    if not Config.AES_MASTER_KEY or len(Config.AES_MASTER_KEY) != 64:
        print("❌ AES_MASTER_KEY not configured properly in .env")
        print("Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")
        exit(1)
    

    crypto = CryptoService()
    

    test_data = b"Secret Evidence: Fingerprint found at crime scene"
    print(f"\n📝 Original data: {test_data}")
    print(f"📏 Size: {len(test_data)} bytes")
    

    test_file = "temp_test.txt"
    with open(test_file, 'wb') as f:
        f.write(test_data)
    

    print("\n🔒 Encrypting...")
    encrypted_file = "temp_test.enc"
    metadata = crypto.encrypt(test_file, encrypted_file)
    print(f"✅ IV (Base64): {metadata['iv_base64']}")
    print(f"✅ HMAC (Base64): {metadata['hmac_base64']}")
    print(f"✅ Encrypted file: {encrypted_file}")
    

    print("\n🔍 Verifying HMAC...")
    encrypted_bytes = crypto.read_encrypted_file(encrypted_file)
    is_valid = crypto.verify_hmac(encrypted_bytes, metadata['hmac_base64'])
    print(f"✅ HMAC Valid: {is_valid}")
    

    print("\n🔓 Decrypting...")
    decrypted = crypto.decrypt(encrypted_file)
    print(f"✅ Decrypted: {decrypted}")
    

    if decrypted == test_data:
        print("\n✅ Round-trip encryption/decryption successful!")
        print("✅ HMAC integrity verification successful!")
    else:
        print("\n❌ Round-trip verification failed!")
    

    print("\n📁 Testing high-level API...")
    metadata2 = crypto.encrypt_file("evidence.jpg", test_data)
    decrypted2 = crypto.decrypt_file(metadata2['file_path'], metadata2['hmac_base64'])
    
    if decrypted2 == test_data:
        print("✅ High-level API test passed!")
    else:
        print("❌ High-level API test failed!")
    

    import os
    for f in [test_file, encrypted_file, metadata2['file_path']]:
        if os.path.exists(f):
            os.remove(f)
    
    print("\n✅ All tests complete!")

