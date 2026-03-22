import requests
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

def handle_response(response):
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP error: {e}, response: {response.text}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    return None

# =========================
# Cases
# =========================

CASE_URL = "http://localhost:8443/api/cases"

def map_case(api_case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps Java API Case → Python-friendly structure
    Keeps compatibility with existing agent code
    """
    return {
        "id": api_case.get("caseId"),
        "title": api_case.get("caseName"),
        "description": api_case.get("description"),
        "created_at": api_case.get("createdAt"),
        "status": api_case.get("status"),
        "case_key": api_case.get("caseKey"),
        "location": api_case.get("location"),
        "coordinates": api_case.get("coordinates"),
        "report_date": api_case.get("reportDate"),
        "crime_time": api_case.get("crimeTime"),
        "team_assigned_id": api_case.get("teamAssignedId")
    }

def add_case(title: str, description: str) -> Optional[Dict[str, Any]]:
    """
    Create a new forensic case via API
    """
    try:
        payload = {
            "caseName": title,   # mapping here
            "description": description,
            "status": "open"
        }

        response = requests.post(f"{CASE_URL}/create", json=payload)
        data = handle_response(response)

        if data:
            mapped = map_case(data)
            logger.info(f"✅ Created case via API: {mapped['id']}")
            return mapped

        return None

    except Exception as e:
        logger.error(f"❌ Error creating case: {e}")
        return None

def get_case(case_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a case by ID via API
    """
    try:
        response = requests.get(f"{CASE_URL}/{case_id}")
        data = handle_response(response)

        if data:
            return map_case(data)

        return None

    except Exception as e:
        logger.error(f"❌ Error retrieving case {case_id}: {e}")
        return None

def get_all_cases() -> List[Dict[str, Any]]:
    """
    Retrieve all cases via API
    """
    try:
        response = requests.get(f"{CASE_URL}/all")
        data = handle_response(response)

        if data:
            return [map_case(case) for case in data]

        return []

    except Exception as e:
        logger.error(f"❌ Error retrieving cases: {e}")
        return []

# =========================
# Suspect API
# =========================

SUSPECTS_URL = "http://localhost:8443/api/suspect"

def map_suspect(api_suspect: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps Java API Suspect → Python-friendly structure
    """
    return {
        "id": api_suspect.get("suspectId"),
        "case_id": api_suspect.get("caseId"),
        "name": api_suspect.get("fullName"),
        "alias": api_suspect.get("alias"),
        "date_of_birth": api_suspect.get("dateOfBirth"),
        "nationality": api_suspect.get("nationality"),
        "profile_text": api_suspect.get("notes"),  # mapping here
        "metadata_json": api_suspect.get("metadataJson"),
        "created_at": api_suspect.get("createdAt"),
    }

def add_suspect(
    case_id: int,
    name: str,
    profile_text: str,
    metadata_json: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Add a suspect via API
    """
    try:
        payload = {
            "caseId": case_id,
            "fullName": name,              # mapping
            "notes": profile_text,        # mapping
            "metadataJson": metadata_json or {}
        }

        response = requests.post(f"{SUSPECTS_URL}/create", json=payload)
        data = handle_response(response)

        if data:
            mapped = map_suspect(data)
            logger.info(f"✅ Added suspect via API: {mapped['id']}")
            return mapped

        return None

    except Exception as e:
        logger.error(f"❌ Error adding suspect: {e}")
        return None

def get_suspects_by_case(case_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve suspects for a case via API
    """
    try:
        response = requests.get(f"{SUSPECTS_URL}/case/{case_id}")
        data = handle_response(response)

        if data:
            return [map_suspect(s) for s in data]

        return []

    except Exception as e:
        logger.error(f"❌ Error retrieving suspects for case {case_id}: {e}")
        return []

# =========================
# Image API
# =========================

IMAGE_URL = "https://localhost:8443/api/image"

def map_image(api_image: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": api_image.get("imageId"),
        "filename": api_image.get("filename"),
        "file_path": api_image.get("filepath"),
        "iv_hex": api_image.get("ivBase64"),
        "sha256_hex": api_image.get("hmacBase64"),  # mapped (HMAC instead of SHA)
        "created_at": api_image.get("uploadedAt"),
        "view_url": api_image.get("viewUrl"),
        "verify_url": api_image.get("verifyUrl"),
    }

def add_image(case_id, filename, file_path, iv_hex, sha256_hex):
    try:
        response = requests.post(
            f"{IMAGE_URL}/add",
            json={
                "caseId": case_id,
                "filename": filename,
                "filepath": file_path,
                "ivBase64": iv_hex,
                "hmacBase64": sha256_hex
            }
        )

        if response.status_code == 201:
            return response.json()
        else:
            logger.error(f"❌ Failed to add image: {response.text}")
            return None

    except Exception as e:
        logger.error(f"❌ Error calling add_image endpoint: {e}")
        return None

def get_images_by_case(case_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve images for a case via API
    """
    try:
        response = requests.get(f"{IMAGE_URL}/list/{case_id}")
        data = handle_response(response)

        if data:
            return [map_image(img) for img in data]

        return []

    except Exception as e:
        logger.error(f"❌ Error retrieving images for case {case_id}: {e}")
        return []

def delete_image(image_id: int) -> bool:
    """
    Delete image via API (DB + file handled in backend)
    """
    try:
        response = requests.delete(f"{IMAGE_URL}/{image_id}")

        if response.status_code in (200, 204):
            logger.info(f"✅ Deleted image via API: {image_id}")
            return True

        logger.warning(f"⚠️ Failed to delete image {image_id}: {response.text}")
        return False

    except Exception as e:
        logger.error(f"❌ Error deleting image {image_id}: {e}")
        return False