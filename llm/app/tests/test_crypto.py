"""
Unit tests for AES-256-CBC encryption/decryption module
Tests security, integrity, and error handling
"""

import pytest
import os
import secrets
from pathlib import Path

from app.security.crypto import (
    encrypt_bytes,
    decrypt_bytes,
    save_encrypted_file,
    decrypt_file_to_bytes,
    delete_encrypted_file,
    InvalidKeyError,
    DecryptionError,
    IntegrityError,
    CryptoError,
    _validate_key,
    _compute_sha256,
    _generate_iv
)



@pytest.fixture
def valid_key():
    """Generate a valid 32-byte (64 hex char) AES-256 key"""
    return secrets.token_hex(32)


@pytest.fixture
def sample_data():
    """Sample data for encryption tests"""
    return b"Secret forensic evidence: fingerprint analysis results"


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for encrypted files"""
    output_dir = tmp_path / "encrypted"
    output_dir.mkdir()
    return str(output_dir)






def test_validate_key_valid(valid_key):
    """Test that valid keys are accepted"""
    key_bytes = _validate_key(valid_key)
    assert len(key_bytes) == 32
    assert isinstance(key_bytes, bytes)


def test_validate_key_empty():
    """Test that empty key raises InvalidKeyError"""
    with pytest.raises(InvalidKeyError, match="Encryption key is empty"):
        _validate_key("")


def test_validate_key_wrong_length():
    """Test that wrong length key raises InvalidKeyError"""
    short_key = "a" * 32
    with pytest.raises(InvalidKeyError, match="Invalid key length"):
        _validate_key(short_key)


def test_validate_key_invalid_hex():
    """Test that non-hex characters raise InvalidKeyError"""
    invalid_key = "zzzz" + "a" * 60
    with pytest.raises(InvalidKeyError, match="Invalid hex string"):
        _validate_key(invalid_key)






def test_compute_sha256():
    """Test SHA-256 computation"""
    data = b"Test data"
    sha256_hex = _compute_sha256(data)
    

    assert len(sha256_hex) == 64
    assert all(c in '0123456789abcdef' for c in sha256_hex)
    

    assert _compute_sha256(data) == sha256_hex


def test_generate_iv():
    """Test IV generation"""
    iv1 = _generate_iv()
    iv2 = _generate_iv()
    

    assert len(iv1) == 16
    assert len(iv2) == 16
    

    assert iv1 != iv2






def test_encrypt_decrypt_roundtrip(valid_key, sample_data):
    """Test that encryption and decryption produce original data"""

    iv_hex, ciphertext, sha256_hex = encrypt_bytes(sample_data, valid_key)
    

    assert isinstance(iv_hex, str)
    assert len(iv_hex) == 32
    assert isinstance(ciphertext, bytes)
    assert isinstance(sha256_hex, str)
    assert len(sha256_hex) == 64
    

    plaintext = decrypt_bytes(ciphertext, valid_key, iv_hex, sha256_hex)
    

    assert plaintext == sample_data


def test_encrypt_produces_different_ciphertext(valid_key, sample_data):
    """Test that encrypting same data twice produces different ciphertext (due to random IV)"""
    iv1, ciphertext1, sha1 = encrypt_bytes(sample_data, valid_key)
    iv2, ciphertext2, sha2 = encrypt_bytes(sample_data, valid_key)
    

    assert iv1 != iv2
    

    assert ciphertext1 != ciphertext2
    

    assert sha1 == sha2


def test_encrypt_empty_data(valid_key):
    """Test encrypting empty data"""
    empty_data = b""
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(empty_data, valid_key)
    

    assert len(ciphertext) > 0
    

    plaintext = decrypt_bytes(ciphertext, valid_key, iv_hex)
    assert plaintext == empty_data


def test_encrypt_large_data(valid_key):
    """Test encrypting large data (1MB)"""
    large_data = os.urandom(1024 * 1024)
    
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(large_data, valid_key)
    plaintext = decrypt_bytes(ciphertext, valid_key, iv_hex, sha256_hex)
    
    assert plaintext == large_data






def test_decrypt_with_wrong_key(valid_key, sample_data):
    """Test that decryption with wrong key raises DecryptionError"""

    iv_hex, ciphertext, sha256_hex = encrypt_bytes(sample_data, valid_key)
    

    wrong_key = secrets.token_hex(32)
    
    with pytest.raises(DecryptionError, match="incorrect key or IV"):
        decrypt_bytes(ciphertext, wrong_key, iv_hex)


def test_decrypt_with_invalid_key_format(sample_data):
    """Test that decryption with invalid key format raises InvalidKeyError"""

    valid_key = secrets.token_hex(32)
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(sample_data, valid_key)
    

    invalid_key = "not_a_valid_hex_key"
    
    with pytest.raises(InvalidKeyError):
        decrypt_bytes(ciphertext, invalid_key, iv_hex)






def test_decrypt_with_wrong_iv(valid_key, sample_data):
    """Test that decryption with wrong IV raises DecryptionError"""

    iv_hex, ciphertext, sha256_hex = encrypt_bytes(sample_data, valid_key)
    

    wrong_iv = secrets.token_hex(16)
    
    with pytest.raises(DecryptionError, match="incorrect key or IV"):
        decrypt_bytes(ciphertext, valid_key, wrong_iv)


def test_decrypt_with_invalid_iv_format(valid_key, sample_data):
    """Test that decryption with invalid IV format raises InvalidKeyError"""
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(sample_data, valid_key)
    

    invalid_ivs = [
        "",
        "a" * 16,
        "a" * 64,
        "zzzz" + "a" * 28,
    ]
    
    for invalid_iv in invalid_ivs:
        with pytest.raises(InvalidKeyError):
            decrypt_bytes(ciphertext, valid_key, invalid_iv)






def test_sha256_computed_correctly(valid_key, sample_data):
    """Test that SHA-256 hash is computed correctly"""
    import hashlib
    
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(sample_data, valid_key)
    

    expected_hash = hashlib.sha256(sample_data).hexdigest()
    
    assert sha256_hex == expected_hash


def test_integrity_check_passes(valid_key, sample_data):
    """Test that integrity verification passes with correct SHA-256"""
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(sample_data, valid_key)
    

    plaintext = decrypt_bytes(ciphertext, valid_key, iv_hex, sha256_hex)
    
    assert plaintext == sample_data


def test_integrity_check_fails_on_tampered_data(valid_key, sample_data):
    """Test that integrity verification fails with wrong SHA-256"""
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(sample_data, valid_key)
    

    wrong_sha256 = "a" * 64
    
    with pytest.raises(IntegrityError, match="Data integrity check failed"):
        decrypt_bytes(ciphertext, valid_key, iv_hex, wrong_sha256)


def test_integrity_check_optional(valid_key, sample_data):
    """Test that integrity verification is optional"""
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(sample_data, valid_key)
    

    plaintext = decrypt_bytes(ciphertext, valid_key, iv_hex, verify_sha256=None)
    
    assert plaintext == sample_data






def test_save_encrypted_file(valid_key, sample_data, temp_output_dir):
    """Test saving encrypted file to disk"""
    metadata = save_encrypted_file(
        "evidence.jpg",
        sample_data,
        valid_key,
        output_dir=temp_output_dir
    )
    

    assert "file_path" in metadata
    assert "iv_hex" in metadata
    assert "sha256_hex" in metadata
    assert "original_filename" in metadata
    assert "size_bytes" in metadata
    

    assert Path(metadata["file_path"]).exists()
    

    assert metadata["original_filename"] == "evidence.jpg"
    assert isinstance(metadata["size_bytes"], int)
    assert metadata["size_bytes"] > 0


def test_decrypt_file_to_bytes(valid_key, sample_data, temp_output_dir):
    """Test decrypting file from disk"""

    metadata = save_encrypted_file(
        "test.txt",
        sample_data,
        valid_key,
        output_dir=temp_output_dir
    )
    

    decrypted = decrypt_file_to_bytes(
        metadata["file_path"],
        valid_key,
        metadata["iv_hex"],
        metadata["sha256_hex"]
    )
    
    assert decrypted == sample_data


def test_decrypt_nonexistent_file(valid_key, temp_output_dir):
    """Test that decrypting non-existent file raises FileNotFoundError"""
    fake_path = Path(temp_output_dir) / "nonexistent.enc"
    
    with pytest.raises(FileNotFoundError):
        decrypt_file_to_bytes(str(fake_path), valid_key, "a" * 32)


def test_save_encrypted_file_creates_unique_filenames(valid_key, sample_data, temp_output_dir):
    """Test that saving multiple files creates unique filenames"""
    metadata1 = save_encrypted_file("test.jpg", sample_data, valid_key, temp_output_dir)
    metadata2 = save_encrypted_file("test.jpg", sample_data, valid_key, temp_output_dir)
    

    assert metadata1["file_path"] != metadata2["file_path"]
    

    assert Path(metadata1["file_path"]).exists()
    assert Path(metadata2["file_path"]).exists()


def test_save_encrypted_file_creates_directory(valid_key, sample_data, tmp_path):
    """Test that save_encrypted_file creates directory if missing"""
    non_existent_dir = tmp_path / "new_dir" / "nested"
    
    metadata = save_encrypted_file(
        "test.txt",
        sample_data,
        valid_key,
        output_dir=str(non_existent_dir)
    )
    

    assert non_existent_dir.exists()
    

    assert Path(metadata["file_path"]).exists()


def test_delete_encrypted_file(valid_key, sample_data, temp_output_dir):
    """Test deleting encrypted file"""

    metadata = save_encrypted_file("test.txt", sample_data, valid_key, temp_output_dir)
    file_path = metadata["file_path"]
    

    assert Path(file_path).exists()
    

    success = delete_encrypted_file(file_path)
    
    assert success is True
    assert not Path(file_path).exists()


def test_delete_nonexistent_file(temp_output_dir):
    """Test deleting non-existent file returns False"""
    fake_path = Path(temp_output_dir) / "nonexistent.enc"
    success = delete_encrypted_file(str(fake_path))
    
    assert success is False






def test_complete_file_workflow(valid_key, temp_output_dir):
    """Test complete workflow: save → decrypt → verify → delete"""
    original_data = b"Complete forensic evidence chain of custody test"
    

    metadata = save_encrypted_file(
        "evidence_001.jpg",
        original_data,
        valid_key,
        output_dir=temp_output_dir
    )
    

    assert Path(metadata["file_path"]).exists()
    

    decrypted = decrypt_file_to_bytes(
        metadata["file_path"],
        valid_key,
        metadata["iv_hex"],
        metadata["sha256_hex"]
    )
    assert decrypted == original_data
    

    success = delete_encrypted_file(metadata["file_path"])
    assert success is True
    assert not Path(metadata["file_path"]).exists()






def test_encrypt_with_invalid_key_type():
    """Test that encrypting with non-string key raises appropriate error"""
    with pytest.raises((InvalidKeyError, TypeError, AttributeError)):
        encrypt_bytes(b"data", 12345)


def test_encrypt_with_none_data(valid_key):
    """Test that encrypting None raises appropriate error"""
    with pytest.raises((TypeError, AttributeError)):
        encrypt_bytes(None, valid_key)


def test_decrypt_with_none_ciphertext(valid_key):
    """Test that decrypting None raises appropriate error"""
    with pytest.raises((TypeError, AttributeError)):
        decrypt_bytes(None, valid_key, "a" * 32)


def test_decrypt_corrupted_ciphertext(valid_key, sample_data):
    """Test that decrypting corrupted ciphertext raises DecryptionError"""
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(sample_data, valid_key)
    

    corrupted = ciphertext[:-5] + b"XXXXX"
    
    with pytest.raises(DecryptionError):
        decrypt_bytes(corrupted, valid_key, iv_hex)






def test_encrypt_special_characters(valid_key):
    """Test encrypting data with special characters"""
    special_data = b"\x00\x01\xff\xfe" + "Special 你好 🔐".encode('utf-8')
    
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(special_data, valid_key)
    plaintext = decrypt_bytes(ciphertext, valid_key, iv_hex)
    
    assert plaintext == special_data


def test_encrypt_binary_image_data(valid_key):
    """Test encrypting binary image-like data"""

    jpeg_header = b'\xff\xd8\xff\xe0'
    binary_data = jpeg_header + os.urandom(1000)
    
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(binary_data, valid_key)
    plaintext = decrypt_bytes(ciphertext, valid_key, iv_hex, sha256_hex)
    
    assert plaintext == binary_data
    assert plaintext.startswith(jpeg_header)


def test_multiple_encryptions_with_same_key(valid_key):
    """Test that same key can be reused for multiple encryptions"""
    data1 = b"Evidence A"
    data2 = b"Evidence B"
    data3 = b"Evidence C"
    

    iv1, cipher1, sha1 = encrypt_bytes(data1, valid_key)
    iv2, cipher2, sha2 = encrypt_bytes(data2, valid_key)
    iv3, cipher3, sha3 = encrypt_bytes(data3, valid_key)
    

    plain1 = decrypt_bytes(cipher1, valid_key, iv1)
    plain2 = decrypt_bytes(cipher2, valid_key, iv2)
    plain3 = decrypt_bytes(cipher3, valid_key, iv3)
    
    assert plain1 == data1
    assert plain2 == data2
    assert plain3 == data3






def test_ciphertext_appears_random(valid_key):
    """Test that ciphertext has no obvious patterns"""

    structured_data = b"A" * 100
    
    iv_hex, ciphertext, sha256_hex = encrypt_bytes(structured_data, valid_key)
    

    assert b"AAA" not in ciphertext
    

    assert ciphertext != structured_data


def test_iv_uniqueness(valid_key, sample_data):
    """Test that IVs are unique across multiple encryptions"""
    ivs = set()
    
    for _ in range(100):
        iv_hex, _, _ = encrypt_bytes(sample_data, valid_key)
        ivs.add(iv_hex)
    

    assert len(ivs) == 100


def test_ciphertext_length_calculation(valid_key):
    """Test that ciphertext length follows AES block size rules"""
    for plaintext_len in [1, 15, 16, 17, 31, 32, 33]:
        data = b"X" * plaintext_len
        _, ciphertext, _ = encrypt_bytes(data, valid_key)
        

        assert len(ciphertext) % 16 == 0
        

        import math
        expected_blocks = math.ceil(plaintext_len / 16) + (1 if plaintext_len % 16 == 0 else 0)
        expected_length = expected_blocks * 16
        

        assert len(ciphertext) >= plaintext_len
        assert len(ciphertext) <= plaintext_len + 16

