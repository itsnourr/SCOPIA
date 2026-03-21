"""
Image Analyzer Tool with Vision AI for Forensic Crime Analysis Agent

This tool:
1. Decrypts encrypted evidence images (in-memory only)
2. Extracts EXIF metadata (datetime, GPS, camera info)
3. Analyzes image content using Google Gemini Vision AI
   - Identifies objects, people, locations
   - Detects potential evidence (weapons, blood, disturbances)
   - Reads visible text (signs, plates, labels)
4. Generates comprehensive captions (vision analysis + metadata)
5. Updates database with analysis results
6. Prepares data for RAG indexing

Security: Decrypted image bytes are kept in memory only - never written to disk.

Example Usage:
    >>> from app.tools.image_analyzer import analyze_image
    >>> 
    >>> # Analyze an image (by database ID)
    >>> result = analyze_image(image_id=1)
    >>> 
    >>> print(result['caption'])
    >>> # "The image shows a kitchen knife with dark red stains on a wooden table. 
    >>> #  A broken window is visible in the background. The scene appears to be 
    >>> #  indoors in a residential setting. Captured on 2024-03-15 14:23:10 
    >>> #  with iPhone 14 Pro at 40.7128°N, 74.0060°W."
    >>> 
    >>> print(result['exif'])
    >>> # {'datetime': '2024-03-15 14:23:10', 'gps': {'lat': 40.7128, 'lon': -74.0060}, ...}

Integration Hook:
    After uploading a new image in the UI:
    
    1. Upload and encrypt image -> store in database
    2. Call analyze_image(image_id) -> Vision AI + EXIF analysis
    3. Call build_case_index(case_id) -> index caption in RAG
"""

import io
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import exifread
import google.generativeai as genai
import base64

from config import Config
from app.security import get_crypto_service
from app.db import get_images_by_case
from app.db.dao import update_image_analysis, get_db_session
from app.db.models import Image as ImageModel


logger = logging.getLogger(__name__)


class ImageAnalysisError(Exception):
    """Base exception for image analysis errors"""
    pass


class DecryptionError(ImageAnalysisError):
    """Raised when image decryption fails"""
    pass


class EXIFExtractionError(ImageAnalysisError):
    """Raised when EXIF extraction fails (non-critical)"""
    pass


def _convert_to_degrees(value: Any) -> Optional[float]:
    """
    Convert GPS coordinates to decimal degrees
    
    Args:
        value: GPS coordinate value (from EXIF)
        
    Returns:
        Decimal degrees as float, or None if conversion fails
    """
    try:

        if hasattr(value, 'values'):

            d, m, s = value.values
            return float(d.num) / float(d.den) + \
                   (float(m.num) / float(m.den)) / 60.0 + \
                   (float(s.num) / float(s.den)) / 3600.0
        elif isinstance(value, (list, tuple)) and len(value) >= 3:

            d, m, s = value
            if isinstance(d, tuple):
                d = d[0] / d[1] if d[1] != 0 else d[0]
            if isinstance(m, tuple):
                m = m[0] / m[1] if m[1] != 0 else m[0]
            if isinstance(s, tuple):
                s = s[0] / s[1] if s[1] != 0 else s[0]
            return float(d) + float(m) / 60.0 + float(s) / 3600.0
        else:
            return None
    except (AttributeError, ValueError, ZeroDivisionError, TypeError) as e:
        logger.debug(f"GPS coordinate conversion failed: {e}")
        return None


def _extract_gps_from_exif(exif_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Extract GPS coordinates from EXIF data
    
    Args:
        exif_data: Raw EXIF data dictionary
        
    Returns:
        Dictionary with 'lat' and 'lon' keys, or None if GPS not available
    """
    try:

        if 'GPSInfo' in exif_data:
            gps_info = exif_data['GPSInfo']
            
            lat = None
            lon = None
            lat_ref = None
            lon_ref = None
            

            if 2 in gps_info:
                lat = _convert_to_degrees(gps_info[2])
            if 4 in gps_info:
                lon = _convert_to_degrees(gps_info[4])
            if 1 in gps_info:
                lat_ref = gps_info[1]
            if 3 in gps_info:
                lon_ref = gps_info[3]
            

            if lat is not None and lat_ref == 'S':
                lat = -lat
            if lon is not None and lon_ref == 'W':
                lon = -lon
            
            if lat is not None and lon is not None:
                return {'lat': round(lat, 6), 'lon': round(lon, 6)}
        

        if 'GPS GPSLatitude' in exif_data and 'GPS GPSLongitude' in exif_data:
            lat = _convert_to_degrees(exif_data['GPS GPSLatitude'])
            lon = _convert_to_degrees(exif_data['GPS GPSLongitude'])
            

            if 'GPS GPSLatitudeRef' in exif_data and exif_data['GPS GPSLatitudeRef'].values == 'S':
                lat = -lat if lat else None
            if 'GPS GPSLongitudeRef' in exif_data and exif_data['GPS GPSLongitudeRef'].values == 'W':
                lon = -lon if lon else None
            
            if lat is not None and lon is not None:
                return {'lat': round(lat, 6), 'lon': round(lon, 6)}
        
        return None
        
    except Exception as e:
        logger.warning(f"GPS extraction failed: {e}")
        return None


def extract_exif(file_path: str, key_hex: str, iv_hex: str) -> Dict[str, Any]:
    """
    Decrypt image file in-memory and extract EXIF metadata
    
    Args:
        file_path: Path to encrypted image file
        key_hex: Encryption key (hex string)
        iv_hex: Initialization vector (hex string)
        
    Returns:
        Dictionary with extracted EXIF data:
            - datetime: Image capture datetime (ISO format string)
            - gps: GPS coordinates {'lat': float, 'lon': float} or None
            - camera: Camera model string or None
            - width: Image width in pixels
            - height: Image height in pixels
            - raw: Raw EXIF data dictionary
            
    Raises:
        DecryptionError: If image decryption fails
        EXIFExtractionError: If EXIF parsing fails (non-critical)
        
    Example:
        >>> exif = extract_exif("/path/to/image.enc", key_hex, iv_hex)
        >>> print(exif['datetime'])
        '2024-03-15 14:23:10'
        >>> print(exif['gps'])
        {'lat': 40.7128, 'lon': -74.0060}
    """
    logger.info(f"📸 Extracting EXIF from: {Path(file_path).name}")
    
    try:

        crypto = get_crypto_service()
        
        try:
            decrypted_bytes = crypto.decrypt_file(file_path, stored_hmac_base64=None)
        except Exception as e:
            logger.error(f"Failed to decrypt image: {e}")
            raise DecryptionError(f"Image decryption failed: {e}")
        
        logger.debug(f"Decrypted {len(decrypted_bytes)} bytes")
        

        exif_dict = {}
        
        try:

            image = Image.open(io.BytesIO(decrypted_bytes))
            

            width, height = image.size
            exif_dict['width'] = width
            exif_dict['height'] = height
            

            exif_data = image.getexif()
            
            if exif_data:

                raw_exif = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    raw_exif[tag] = str(value) if not isinstance(value, (str, int, float)) else value
                

                gps_info = exif_data.get_ifd(0x8825)
                if gps_info:
                    raw_exif['GPSInfo'] = gps_info
                
                exif_dict['raw'] = raw_exif
                

                

                datetime_str = None
                for dt_key in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                    if dt_key in raw_exif:
                        datetime_str = raw_exif[dt_key]
                        break
                
                if datetime_str:
                    try:

                        dt = datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S')
                        exif_dict['datetime'] = dt.isoformat()
                    except ValueError:
                        exif_dict['datetime'] = datetime_str
                else:
                    exif_dict['datetime'] = None
                

                camera = raw_exif.get('Model') or raw_exif.get('Make')
                exif_dict['camera'] = camera
                

                gps = _extract_gps_from_exif(raw_exif)
                exif_dict['gps'] = gps
                
                logger.info(f"✅ EXIF extracted: datetime={exif_dict.get('datetime')}, camera={camera}, gps={gps is not None}")
                
            else:

                logger.info("⚠️  No EXIF data found in image")
                exif_dict['datetime'] = None
                exif_dict['camera'] = None
                exif_dict['gps'] = None
                exif_dict['raw'] = {}
        
        except Exception as e:
            logger.warning(f"Pillow EXIF extraction failed, trying exifread: {e}")
            

            try:
                tags = exifread.process_file(io.BytesIO(decrypted_bytes), details=False)
                
                if tags:
                    raw_exif = {k: str(v) for k, v in tags.items()}
                    exif_dict['raw'] = raw_exif
                    

                    datetime_str = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
                    if datetime_str:
                        exif_dict['datetime'] = str(datetime_str)
                    else:
                        exif_dict['datetime'] = None
                    

                    camera = tags.get('Image Model') or tags.get('Image Make')
                    exif_dict['camera'] = str(camera) if camera else None
                    

                    gps = _extract_gps_from_exif(tags)
                    exif_dict['gps'] = gps
                    
                    logger.info(f"✅ EXIF extracted via exifread")
                else:

                    exif_dict['datetime'] = None
                    exif_dict['camera'] = None
                    exif_dict['gps'] = None
                    exif_dict['raw'] = {}
                    logger.info("⚠️  No EXIF data found (exifread)")
                    
            except Exception as e2:
                logger.warning(f"exifread also failed: {e2}")

                exif_dict['datetime'] = None
                exif_dict['camera'] = None
                exif_dict['gps'] = None
                exif_dict['raw'] = {}
        
        return exif_dict
        
    except DecryptionError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during EXIF extraction: {e}")
        raise EXIFExtractionError(f"EXIF extraction failed: {e}")


def analyze_image_content_with_vision(image_bytes: bytes) -> Optional[str]:
    """
    Analyze image content using Google Gemini Vision API
    
    Args:
        image_bytes: Decrypted image bytes
        
    Returns:
        Detailed description of image content, or None if analysis fails
        
    Example:
        >>> description = analyze_image_content_with_vision(image_bytes)
        >>> print(description)
        'The image shows a kitchen knife with dark stains on a wooden table. 
         A broken window is visible in the background. The scene appears to be 
         indoors in a residential setting.'
    """
    try:

        if not Config.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured, skipping vision analysis")
            return None
        

        genai.configure(api_key=Config.GEMINI_API_KEY)
        

        model = genai.GenerativeModel(Config.GEMINI_MODEL)
        

        image = Image.open(io.BytesIO(image_bytes))
        

        prompt = """You are a forensic evidence analyst. Analyze this image in detail for a criminal investigation.

ETHICAL USE & RESPONSIBILITY:
- This system is for legitimate law enforcement and forensic investigation purposes only
- Provide objective, factual analysis based only on what is visible in the image
- Do not speculate, infer, or make assumptions beyond what is clearly visible
- Maintain professional standards and ethical conduct at all times
- All analysis is decision support only, not a legal conclusion

REQUIRED FORMAT - You MUST follow this exact structure:

First, provide a one-sentence main caption describing the overall scene.

Then, provide categorized details using these exact bold headers:

**Objects**: [Describe what items are visible - weapons, personal belongings, documents, vehicles, etc. If none, state "No objects are visible."]

**People**: [Describe any people visible - appearance, clothing, actions, positions. If none, state "No people are visible in the image."]

**Location**: [Describe the type of location - indoor/outdoor, residential/commercial, room type, setting. Be specific.]

**Evidence**: [Describe any potential forensic evidence - blood, damage, disturbance, suspicious items, crime-related objects. If none, state "No apparent forensic evidence such as blood, damage, debris, or suspicious items."]

**Text**: [Describe any visible text, signs, license plates, labels, documents. If none, state "No discernible text, signs, or license plates are visible."]

**Condition**: [Describe overall scene condition - orderly/disturbed, lighting, time of day if apparent, state of objects, cleanliness. Be specific about what you observe.]

CRITICAL: You MUST use the exact format above with bold headers (**Objects**, **People**, etc.) and provide information for ALL categories, even if stating "No [category] visible." Be specific, objective, and factual."""

        logger.info("🔍 Analyzing image content with Gemini Vision...")
        

        response = model.generate_content([prompt, image])
        
        if response and response.text:
            description = response.text.strip()
            logger.info(f"✅ Vision analysis complete: {description[:100]}...")
            return description
        else:
            logger.warning("Vision API returned empty response")
            return None
            
    except Exception as e:
        logger.warning(f"Vision analysis failed (will use metadata-only caption): {e}")
        return None


def generate_caption(filename: str, exif: Optional[Dict[str, Any]] = None, vision_description: Optional[str] = None) -> str:
    """
    Generate a descriptive caption for an evidence image
    
    Args:
        filename: Original image filename
        exif: EXIF data dictionary (from extract_exif), or None
        vision_description: AI-generated description of image content, or None
        
    Returns:
        Comprehensive caption describing the image
        
    Example:
        >>> # With vision + EXIF
        >>> caption = generate_caption("evidence.jpg", exif, "Kitchen knife with dark stains...")
        >>> print(caption)
        'Kitchen knife with dark stains on wooden table. Captured on 2024-03-15 14:23:10 
         with iPhone 14 Pro at 40.7128°N, 74.0060°W.'
    """
    logger.debug(f"Generating caption for: {filename}")
    

    if vision_description:
        caption = vision_description
        

        metadata_parts = []
        
        if exif:
            if exif.get('datetime'):
                datetime_str = exif['datetime']
                try:
                    if 'T' in datetime_str:
                        dt = datetime.fromisoformat(datetime_str)
                        datetime_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
                metadata_parts.append(f"captured on {datetime_str}")
            
            if exif.get('camera'):
                metadata_parts.append(f"with {exif['camera']}")
            
            if exif.get('gps'):
                lat = exif['gps']['lat']
                lon = exif['gps']['lon']
                lat_dir = 'N' if lat >= 0 else 'S'
                lon_dir = 'E' if lon >= 0 else 'W'
                metadata_parts.append(f"at {abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}")
        
        if metadata_parts:

            metadata_text = " ".join(metadata_parts).capitalize() + "."
            caption += f"\n\n**Metadata**: {metadata_text}"
    
    else:

        parts = []
        
        if exif and any([exif.get('datetime'), exif.get('camera'), exif.get('gps')]):

            parts.append("Evidence photo")
            

            if exif.get('datetime'):
                datetime_str = exif['datetime']
                try:
                    if 'T' in datetime_str:
                        dt = datetime.fromisoformat(datetime_str)
                        datetime_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
                parts.append(f"taken on {datetime_str}")
            

            if exif.get('camera'):
                parts.append(f"with {exif['camera']}")
            

            if exif.get('gps'):
                lat = exif['gps']['lat']
                lon = exif['gps']['lon']
                lat_dir = 'N' if lat >= 0 else 'S'
                lon_dir = 'E' if lon >= 0 else 'W'
                parts.append(f"at location {abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}")
            
            caption = " ".join(parts) + "."
            

            if exif.get('width') and exif.get('height'):
                caption += f" Image dimensions: {exif['width']}x{exif['height']} pixels."
        
        else:

            name = Path(filename).stem
            name_clean = name.replace('_', ' ').replace('-', ' ')
            caption = f"Evidence photo: {name_clean} (no metadata available)."
    
    logger.info(f"✅ Caption generated: {caption[:80]}...")
    return caption


def analyze_image(image_id: int) -> Dict[str, Any]:
    """
    Complete image analysis workflow with Vision AI
    
    Steps:
    1. Load image record from database (file_path, iv_hex)
    2. Decrypt image bytes in memory
    3. Extract EXIF metadata (date, GPS, camera)
    4. Analyze image content with Gemini Vision AI (objects, people, scene)
    5. Generate comprehensive caption (vision + metadata)
    6. Update database with results
    7. Return analysis summary
    
    Args:
        image_id: Database ID of image to analyze
        
    Returns:
        Dictionary with analysis results:
            - image_id: Database ID
            - filename: Original filename
            - caption: Generated caption
            - exif: Extracted EXIF data
            - success: Whether analysis succeeded
            - error: Error message if failed
            
    Raises:
        ValueError: If image_id not found in database
        DecryptionError: If image decryption fails
        
    Example:
        >>> from app.tools.image_analyzer import analyze_image
        >>> 
        >>> # Analyze image
        >>> result = analyze_image(image_id=1)
        >>> 
        >>> if result['success']:
        ...     print(f"Caption: {result['caption']}")
        ...     print(f"EXIF: {result['exif']}")
        ... else:
        ...     print(f"Error: {result['error']}")
        
        >>> # Caption is now stored in database and ready for RAG indexing
        >>> from app.rag import build_case_index
        >>> build_case_index(case_id=1)  # Index caption for semantic search
    """
    logger.info(f"🔍 Analyzing image ID: {image_id}")
    
    try:

        with get_db_session() as session:
            image = session.query(ImageModel).filter(ImageModel.id == image_id).first()
            
            if not image:
                raise ValueError(f"Image with ID {image_id} not found in database")
            

            file_path = image.file_path
            iv_hex = image.iv_hex
            filename = image.filename
            case_id = image.case_id
            
            logger.info(f"📁 Loaded image: {filename} (case {case_id})")
        

        crypto = get_crypto_service()
        try:
            decrypted_bytes = crypto.decrypt_file(file_path, stored_hmac_base64=None)
            logger.debug(f"Decrypted {len(decrypted_bytes)} bytes")
        except Exception as e:
            logger.error(f"Decryption failed for image {image_id}: {e}")
            raise DecryptionError(f"Image decryption failed: {e}")
        

        try:
            exif_data = extract_exif(
                file_path=file_path,
                key_hex=Config.AES_MASTER_KEY,
                iv_hex=iv_hex
            )
        except DecryptionError as e:
            logger.error(f"Decryption failed for image {image_id}: {e}")
            raise
        except EXIFExtractionError as e:

            logger.warning(f"EXIF extraction failed, using empty EXIF: {e}")
            exif_data = {
                'datetime': None,
                'camera': None,
                'gps': None,
                'raw': {}
            }
        

        vision_description = analyze_image_content_with_vision(decrypted_bytes)
        

        caption = generate_caption(filename, exif_data, vision_description)
        

        success = update_image_analysis(
            image_id=image_id,
            exif_json=exif_data,
            caption_text=caption
        )
        
        if not success:
            logger.error(f"Failed to update database for image {image_id}")
            return {
                'image_id': image_id,
                'filename': filename,
                'caption': None,
                'exif': None,
                'success': False,
                'error': "Database update failed"
            }
        
        logger.info(f"✅ Image analysis complete for ID {image_id}")
        logger.info(f"   Caption: {caption[:100]}...")
        

        return {
            'image_id': image_id,
            'filename': filename,
            'caption': caption,
            'exif': exif_data,
            'success': True,
            'error': None
        }
        
    except ValueError as e:
        logger.error(f"Image not found: {e}")
        return {
            'image_id': image_id,
            'filename': None,
            'caption': None,
            'exif': None,
            'success': False,
            'error': str(e)
        }
    
    except DecryptionError as e:
        logger.error(f"Decryption error: {e}")
        return {
            'image_id': image_id,
            'filename': filename if 'filename' in locals() else None,
            'caption': None,
            'exif': None,
            'success': False,
            'error': f"Decryption failed: {e}"
        }
    
    except Exception as e:
        logger.error(f"Unexpected error analyzing image {image_id}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'image_id': image_id,
            'filename': filename if 'filename' in locals() else None,
            'caption': None,
            'exif': None,
            'success': False,
            'error': f"Analysis failed: {e}"
        }


def batch_analyze_images(case_id: int) -> Dict[str, Any]:
    """
    Analyze all images for a case
    
    Args:
        case_id: Case ID
        
    Returns:
        Dictionary with batch analysis results:
            - total: Total images found
            - analyzed: Images successfully analyzed
            - failed: Images that failed analysis
            - results: List of individual results
    """
    logger.info(f"📊 Batch analyzing images for case {case_id}")
    
    images = get_images_by_case(case_id)
    
    if not images:
        logger.info(f"No images found for case {case_id}")
        return {
            'total': 0,
            'analyzed': 0,
            'failed': 0,
            'results': []
        }
    
    results = []
    analyzed_count = 0
    failed_count = 0
    
    for image in images:

        if image.caption_text and image.exif_json:
            logger.debug(f"Skipping already analyzed image: {image.filename}")
            analyzed_count += 1
            continue
        
        result = analyze_image(image.id)
        results.append(result)
        
        if result['success']:
            analyzed_count += 1
        else:
            failed_count += 1
    
    logger.info(f"✅ Batch analysis complete: {analyzed_count} analyzed, {failed_count} failed")
    
    return {
        'total': len(images),
        'analyzed': analyzed_count,
        'failed': failed_count,
        'results': results
    }



if __name__ == "__main__":
    """
    Quick test of image analyzer
    Run with: python -m app.tools.image_analyzer
    """
    print("=" * 60)
    print("Image Analyzer Test")
    print("=" * 60)
    
    from app.db import get_all_cases
    
    cases = get_all_cases()
    
    if not cases:
        print("\n⚠️  No cases found in database")
        print("Run: python example_db_usage.py to create sample data")
        exit(0)
    

    case_with_images = None
    for case in cases:
        images = get_images_by_case(case.id)
        if images:
            case_with_images = case
            break
    
    if not case_with_images:
        print("\n⚠️  No images found in any case")
        print("Add images to database first")
        exit(0)
    
    print(f"\n📁 Found case with images: {case_with_images.title}")
    
    images = get_images_by_case(case_with_images.id)
    print(f"📸 Analyzing {len(images)} images...")
    
    for image in images:
        print(f"\n🔍 Analyzing: {image.filename}")
        result = analyze_image(image.id)
        
        if result['success']:
            print(f"   ✅ Success!")
            print(f"   Caption: {result['caption']}")
            if result['exif'].get('datetime'):
                print(f"   DateTime: {result['exif']['datetime']}")
            if result['exif'].get('camera'):
                print(f"   Camera: {result['exif']['camera']}")
            if result['exif'].get('gps'):
                print(f"   GPS: {result['exif']['gps']}")
        else:
            print(f"   ❌ Failed: {result['error']}")
    
    print("\n✅ Image analyzer test complete!")

