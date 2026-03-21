"""
Unit tests for Image Analyzer tool
Tests EXIF extraction, caption generation, and database integration
"""

import pytest
import io
import tempfile
from pathlib import Path
from datetime import datetime
from PIL import Image as PILImage
from PIL.ExifTags import TAGS

from app.tools.image_analyzer import (
    extract_exif,
    generate_caption,
    analyze_image,
    batch_analyze_images,
    DecryptionError,
    EXIFExtractionError
)
from app.security import get_crypto_service
from app.db import add_case, add_image
from app.db.dao import update_image_analysis, get_db_session
from app.db.models import Image as ImageModel
from config import Config



@pytest.fixture(scope="function")
def test_case():
    """Create a test case"""
    case = add_case(
        title="Image Analysis Test Case",
        description="Test case for image analyzer"
    )
    yield case


@pytest.fixture(scope="function")
def create_test_image():
    """Factory to create synthetic JPEG images with optional EXIF"""
    def _create(with_exif=True, width=100, height=100):
        """
        Create a synthetic JPEG image
        
        Args:
            with_exif: If True, add EXIF data
            width: Image width
            height: Image height
            
        Returns:
            bytes: JPEG image data
        """

        img = PILImage.new('RGB', (width, height), color='red')
        

        img_bytes = io.BytesIO()
        
        if with_exif:

            exif = img.getexif()
            exif[0x0132] = "2024:03:15 14:23:10"
            exif[0x010F] = "Apple"
            exif[0x0110] = "iPhone 14 Pro"
            
            img.save(img_bytes, format='JPEG', exif=exif)
        else:
            img.save(img_bytes, format='JPEG')
        
        return img_bytes.getvalue()
    
    return _create






def test_extract_exif_with_metadata(test_case, create_test_image, tmp_path):
    """Test extracting EXIF from image with metadata"""

    image_bytes = create_test_image(with_exif=True)
    

    crypto = get_crypto_service()
    temp_file = tmp_path / "test.jpg"
    with open(temp_file, 'wb') as f:
        f.write(image_bytes)
    
    metadata = crypto.encrypt_file("test.jpg", image_bytes, output_dir=str(tmp_path))
    

    exif = extract_exif(
        metadata["file_path"],
        Config.AES_MASTER_KEY,
        metadata["iv_base64"]
    )
    

    assert exif is not None
    assert isinstance(exif, dict)
    assert 'datetime' in exif
    assert 'camera' in exif
    assert 'gps' in exif
    assert 'raw' in exif
    assert 'width' in exif
    assert 'height' in exif
    

    assert exif['width'] == 100
    assert exif['height'] == 100
    

    assert exif['camera'] is not None
    assert 'iPhone' in exif['camera'] or 'Apple' in exif['camera']


def test_extract_exif_without_metadata(test_case, create_test_image, tmp_path):
    """Test extracting EXIF from image without metadata"""

    image_bytes = create_test_image(with_exif=False)
    

    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("test_no_exif.jpg", image_bytes, output_dir=str(tmp_path))
    

    exif = extract_exif(
        metadata["file_path"],
        Config.AES_MASTER_KEY,
        metadata["iv_base64"]
    )
    

    assert exif is not None
    assert exif['datetime'] is None
    assert exif['camera'] is None
    assert exif['gps'] is None
    assert exif['raw'] == {}


def test_extract_exif_with_wrong_key(test_case, create_test_image, tmp_path):
    """Test EXIF extraction with wrong decryption key"""
    image_bytes = create_test_image(with_exif=True)
    

    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("test.jpg", image_bytes, output_dir=str(tmp_path))
    

    wrong_key = "a" * 64
    
    with pytest.raises(DecryptionError):
        extract_exif(
            metadata["file_path"],
            wrong_key,
            metadata["iv_base64"]
        )


def test_extract_exif_with_wrong_iv(test_case, create_test_image, tmp_path):
    """Test EXIF extraction with wrong IV"""
    image_bytes = create_test_image(with_exif=True)
    

    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("test.jpg", image_bytes, output_dir=str(tmp_path))
    

    wrong_iv = "b" * 32
    
    with pytest.raises(DecryptionError):
        extract_exif(
            metadata["file_path"],
            Config.AES_MASTER_KEY,
            wrong_iv
        )


def test_extract_exif_corrupted_ciphertext(test_case, create_test_image, tmp_path):
    """Test EXIF extraction with corrupted encrypted file"""
    image_bytes = create_test_image(with_exif=True)
    

    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("test.jpg", image_bytes, output_dir=str(tmp_path))
    

    file_path = Path(metadata["file_path"])
    with open(file_path, 'rb') as f:
        encrypted_bytes = bytearray(f.read())
    

    encrypted_bytes[50] ^= 0xFF
    encrypted_bytes[100] ^= 0xFF
    
    with open(file_path, 'wb') as f:
        f.write(bytes(encrypted_bytes))
    

    with pytest.raises((DecryptionError, Exception)):
        extract_exif(
            metadata["file_path"],
            Config.AES_MASTER_KEY,
            metadata["iv_base64"]
        )






def test_generate_caption_with_full_exif():
    """Test caption generation with complete EXIF data"""
    exif = {
        'datetime': '2024-03-15 14:23:10',
        'camera': 'iPhone 14 Pro',
        'gps': {'lat': 40.7128, 'lon': -74.0060},
        'width': 1920,
        'height': 1080
    }
    
    caption = generate_caption("evidence.jpg", exif)
    
    assert isinstance(caption, str)
    assert len(caption) > 0
    assert '2024-03-15' in caption
    assert 'iPhone 14 Pro' in caption
    assert '40.7128' in caption or '40.71' in caption
    assert '1920x1080' in caption


def test_generate_caption_with_partial_exif():
    """Test caption generation with partial EXIF data"""
    exif = {
        'datetime': '2024-03-15 14:23:10',
        'camera': None,
        'gps': None,
        'width': 800,
        'height': 600
    }
    
    caption = generate_caption("crime_scene.jpg", exif)
    
    assert isinstance(caption, str)
    assert len(caption) > 0
    assert '2024-03-15' in caption
    assert 'iPhone' not in caption


def test_generate_caption_without_exif():
    """Test caption generation with no EXIF data"""
    caption = generate_caption("security_footage.jpg", None)
    
    assert isinstance(caption, str)
    assert len(caption) > 0
    assert 'security footage' in caption.lower()
    assert 'no metadata' in caption.lower()


def test_generate_caption_with_empty_exif():
    """Test caption generation with empty EXIF dict"""
    exif = {
        'datetime': None,
        'camera': None,
        'gps': None,
        'raw': {}
    }
    
    caption = generate_caption("image.jpg", exif)
    
    assert isinstance(caption, str)
    assert len(caption) > 0
    assert 'no metadata' in caption.lower()


def test_generate_caption_filename_cleaning():
    """Test that caption cleans up filename"""
    caption = generate_caption("crime_scene_photo_001.jpg", None)
    
    assert 'crime scene photo 001' in caption.lower()
    assert '_' not in caption






def test_analyze_image_success(test_case, create_test_image, tmp_path):
    """Test complete image analysis workflow"""

    image_bytes = create_test_image(with_exif=True)
    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("evidence.jpg", image_bytes, output_dir=str(tmp_path))
    

    import base64
    iv_hex = base64.b64decode(metadata["iv_base64"]).hex()
    
    image_record = add_image(
        case_id=test_case.id,
        filename="evidence.jpg",
        file_path=metadata["file_path"],
        iv_hex=iv_hex,
        sha256_hex=metadata["sha256_hex"]
    )
    

    result = analyze_image(image_record.id)
    

    assert result is not None
    assert result['success'] is True
    assert result['error'] is None
    assert result['image_id'] == image_record.id
    assert result['filename'] == "evidence.jpg"
    assert isinstance(result['caption'], str)
    assert len(result['caption']) > 0
    assert isinstance(result['exif'], dict)
    

    with get_db_session() as session:
        updated_image = session.query(ImageModel).filter(
            ImageModel.id == image_record.id
        ).first()
        
        assert updated_image.caption_text is not None
        assert len(updated_image.caption_text) > 0
        assert updated_image.exif_json is not None
        assert isinstance(updated_image.exif_json, dict)


def test_analyze_image_without_exif(test_case, create_test_image, tmp_path):
    """Test analyzing image without EXIF metadata"""

    image_bytes = create_test_image(with_exif=False)
    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("no_exif.jpg", image_bytes, output_dir=str(tmp_path))
    

    import base64
    iv_hex = base64.b64decode(metadata["iv_base64"]).hex()
    
    image_record = add_image(
        case_id=test_case.id,
        filename="no_exif.jpg",
        file_path=metadata["file_path"],
        iv_hex=iv_hex,
        sha256_hex="a" * 64
    )
    

    result = analyze_image(image_record.id)
    

    assert result['success'] is True
    assert result['caption'] is not None
    assert 'no metadata' in result['caption'].lower()
    assert result['exif'] is not None
    assert result['exif']['datetime'] is None


def test_analyze_image_nonexistent(test_case):
    """Test analyzing non-existent image"""
    result = analyze_image(image_id=99999)
    
    assert result['success'] is False
    assert result['error'] is not None
    assert 'not found' in result['error'].lower()


def test_analyze_image_with_wrong_iv(test_case, create_test_image, tmp_path):
    """Test that wrong IV in database causes failure"""

    image_bytes = create_test_image(with_exif=True)
    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("test.jpg", image_bytes, output_dir=str(tmp_path))
    

    wrong_iv_hex = "b" * 32
    
    image_record = add_image(
        case_id=test_case.id,
        filename="test.jpg",
        file_path=metadata["file_path"],
        iv_hex=wrong_iv_hex,
        sha256_hex="a" * 64
    )
    

    result = analyze_image(image_record.id)
    
    assert result['success'] is False
    assert result['error'] is not None
    assert 'decrypt' in result['error'].lower()


def test_analyze_image_does_not_persist_plaintext(test_case, create_test_image, tmp_path):
    """Test that plaintext image is never written to disk"""

    image_bytes = create_test_image(with_exif=True)
    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("secret.jpg", image_bytes, output_dir=str(tmp_path))
    

    import base64
    iv_hex = base64.b64decode(metadata["iv_base64"]).hex()
    
    image_record = add_image(
        case_id=test_case.id,
        filename="secret.jpg",
        file_path=metadata["file_path"],
        iv_hex=iv_hex,
        sha256_hex="a" * 64
    )
    

    files_before = list(tmp_path.glob("*"))
    

    result = analyze_image(image_record.id)
    

    files_after = list(tmp_path.glob("*"))
    

    assert len(files_after) == len(files_before)
    

    jpeg_files = list(tmp_path.glob("*.jpg")) + list(tmp_path.glob("*.jpeg"))

    for f in jpeg_files:
        assert f.suffix == '.enc' or 'enc' in f.name






def test_batch_analyze_images(test_case, create_test_image, tmp_path):
    """Test batch analyzing multiple images"""

    for i in range(3):
        image_bytes = create_test_image(with_exif=(i % 2 == 0))
        crypto = get_crypto_service()
        metadata = crypto.encrypt_file(f"image_{i}.jpg", image_bytes, output_dir=str(tmp_path))
        
        import base64
        iv_hex = base64.b64decode(metadata["iv_base64"]).hex()
        
        add_image(
            case_id=test_case.id,
            filename=f"image_{i}.jpg",
            file_path=metadata["file_path"],
            iv_hex=iv_hex,
            sha256_hex="a" * 64
        )
    

    result = batch_analyze_images(test_case.id)
    
    assert result['total'] == 3
    assert result['analyzed'] == 3
    assert result['failed'] == 0
    assert len(result['results']) > 0


def test_batch_analyze_empty_case(test_case):
    """Test batch analyzing case with no images"""
    result = batch_analyze_images(test_case.id)
    
    assert result['total'] == 0
    assert result['analyzed'] == 0
    assert result['failed'] == 0
    assert result['results'] == []






def test_analyze_updates_database(test_case, create_test_image, tmp_path):
    """Test that analysis properly updates database"""

    image_bytes = create_test_image(with_exif=True, width=1920, height=1080)
    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("hires.jpg", image_bytes, output_dir=str(tmp_path))
    
    import base64
    iv_hex = base64.b64decode(metadata["iv_base64"]).hex()
    
    image_record = add_image(
        case_id=test_case.id,
        filename="hires.jpg",
        file_path=metadata["file_path"],
        iv_hex=iv_hex,
        sha256_hex="a" * 64
    )
    

    with get_db_session() as session:
        img = session.query(ImageModel).filter(ImageModel.id == image_record.id).first()
        assert img.caption_text is None
        assert img.exif_json is None
    

    result = analyze_image(image_record.id)
    assert result['success'] is True
    

    with get_db_session() as session:
        img = session.query(ImageModel).filter(ImageModel.id == image_record.id).first()
        assert img.caption_text is not None
        assert len(img.caption_text) > 0
        assert img.exif_json is not None
        assert img.exif_json.get('width') == 1920
        assert img.exif_json.get('height') == 1080


def test_analyze_does_not_update_on_failure(test_case, create_test_image, tmp_path):
    """Test that database is not updated when analysis fails"""

    image_bytes = create_test_image(with_exif=True)
    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("test.jpg", image_bytes, output_dir=str(tmp_path))
    

    wrong_iv = "c" * 32
    
    image_record = add_image(
        case_id=test_case.id,
        filename="test.jpg",
        file_path=metadata["file_path"],
        iv_hex=wrong_iv,
        sha256_hex="a" * 64
    )
    

    result = analyze_image(image_record.id)
    assert result['success'] is False
    

    with get_db_session() as session:
        img = session.query(ImageModel).filter(ImageModel.id == image_record.id).first()
        assert img.caption_text is None
        assert img.exif_json is None






def test_analyze_large_image(test_case, tmp_path):
    """Test analyzing larger image"""

    large_image_bytes = create_test_image()(with_exif=True, width=3840, height=2160)
    
    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("4k_image.jpg", large_image_bytes, output_dir=str(tmp_path))
    
    import base64
    iv_hex = base64.b64decode(metadata["iv_base64"]).hex()
    
    image_record = add_image(
        case_id=test_case.id,
        filename="4k_image.jpg",
        file_path=metadata["file_path"],
        iv_hex=iv_hex,
        sha256_hex="a" * 64
    )
    

    result = analyze_image(image_record.id)
    
    assert result['success'] is True
    assert result['exif']['width'] == 3840
    assert result['exif']['height'] == 2160


def test_caption_special_characters(test_case):
    """Test caption generation with special characters in filename"""
    caption = generate_caption("crime_scene@#$%_photo!.jpg", None)
    
    assert isinstance(caption, str)
    assert len(caption) > 0


def test_analyze_skips_already_analyzed(test_case, create_test_image, tmp_path):
    """Test that batch analysis skips already analyzed images"""

    image_bytes = create_test_image(with_exif=True)
    crypto = get_crypto_service()
    metadata = crypto.encrypt_file("test.jpg", image_bytes, output_dir=str(tmp_path))
    
    import base64
    iv_hex = base64.b64decode(metadata["iv_base64"]).hex()
    
    image_record = add_image(
        case_id=test_case.id,
        filename="test.jpg",
        file_path=metadata["file_path"],
        iv_hex=iv_hex,
        sha256_hex="a" * 64
    )
    

    analyze_image(image_record.id)
    

    result = batch_analyze_images(test_case.id)
    
    assert result['total'] == 1
    assert result['analyzed'] == 1
    assert result['results'] == []

