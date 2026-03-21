"""
Timeline Event Extractor

Uses LLM to extract time-based events from evidence documents.
Automatically identifies arrivals, departures, sightings, and other time-stamped events.

Example Usage:
    >>> from app.tools.timeline_extractor import extract_timeline_events
    >>> 
    >>> text = "John Doe left the bar at around 9:45 PM. Sarah Wilson arrived at 10:15 PM."
    >>> events = extract_timeline_events(text, "text_3", case_id=1)
    >>> print(events)
    [
        {
            "suspect": "John Doe",
            "event_type": "departure",
            "timestamp": "2025-11-12 21:45:00",
            "confidence": 0.95,
            "raw_text": "John Doe left the bar at around 9:45 PM."
        },
        {
            "suspect": "Sarah Wilson",
            "event_type": "arrival",
            "timestamp": "2025-11-12 22:15:00",
            "confidence": 0.90,
            "raw_text": "Sarah Wilson arrived at 10:15 PM."
        }
    ]
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.llm_factory import create_llm

from config import Config


logger = logging.getLogger(__name__)


VALID_EVENT_TYPES = {
    "arrival", "departure", "seen", "left", "argument", "sound", 
    "cctv_capture", "phone_call", "message", "transaction", "meeting",
    "sighting", "presence", "absence", "contact", "interaction"
}


def extract_timeline_events(text: str, doc_id: str, case_id: int) -> List[Dict[str, Any]]:
    """
    Extract timeline-relevant events from text using LLM.
    
    Args:
        text: The text content to extract events from
        doc_id: Document identifier (e.g., "text_3", "image_1")
        case_id: Case ID for context
        
    Returns:
        List of event dictionaries with keys:
        - suspect: Suspect name (if identified)
        - event_type: Type of event (arrival, departure, etc.)
        - timestamp: Normalized timestamp (ISO format string)
        - confidence: Confidence score (0.0-1.0)
        - raw_text: Original sentence containing the event
    """
    if not Config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not configured for timeline extraction. Returning empty list.")
        return []
    
    if not text or not text.strip():
        return []
    

    prompt = f"""Extract all time-based events from this document.

Document ID: {doc_id}
Case ID: {case_id}

ETHICAL USE & RESPONSIBILITY:
- This system is for legitimate law enforcement and forensic investigation purposes only
- Extract only factual, time-based events from the provided text
- Do not infer events that are not explicitly stated
- Maintain objectivity - extract events as stated, without interpretation
- All analysis is decision support only, not a legal conclusion

Rules:
- Convert all timestamps to 24-hour format (HH:MM)
- Identify suspect name if explicitly mentioned
- Event types: arrival, departure, seen, left, argument, sound, cctv_capture, phone_call, message, transaction, meeting, sighting, presence, absence, contact, interaction
- If no explicit time is mentioned, skip the event
- Output ONLY valid JSON array, no explanations or markdown
- Each event must have: suspect (or null), event_type, timestamp (ISO format: YYYY-MM-DD HH:MM:SS), confidence (0.0-1.0), raw_text
- Use current date context if only time is given (assume today's date)
- Normalize relative times (e.g., "around 9:45 PM" → "21:45:00")

Text:
{text}

Return JSON array:"""

    try:
        llm = create_llm(temperature=0.0)
        
        response = llm.invoke(prompt)
        content = response.content.strip()
        

        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        

        try:
            events = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse timeline extraction JSON: {e}. Content: {content[:200]}...")
            return []
        

        validated_events = []
        for event in events:
            if not isinstance(event, dict):
                continue
            

            if "event_type" not in event or "timestamp" not in event or "raw_text" not in event:
                continue
            

            event_type = event.get("event_type", "").lower()
            if event_type not in VALID_EVENT_TYPES:
                logger.debug(f"Invalid event type '{event_type}', skipping event")
                continue
            

            timestamp_str = event.get("timestamp", "")
            try:

                timestamp = _parse_timestamp(timestamp_str)
                if timestamp is None:
                    logger.debug(f"Could not parse timestamp '{timestamp_str}', skipping event")
                    continue
            except Exception as e:
                logger.warning(f"Error parsing timestamp '{timestamp_str}': {e}")
                continue
            

            confidence = float(event.get("confidence", 1.0))
            confidence = max(0.0, min(1.0, confidence))
            
            validated_event = {
                "suspect": event.get("suspect"),
                "event_type": event_type,
                "timestamp": timestamp.isoformat(),
                "confidence": confidence,
                "raw_text": event.get("raw_text", "")
            }
            
            validated_events.append(validated_event)
            logger.debug(
                f"Extracted timeline event: {event_type} at {timestamp_str} "
                f"(suspect: {validated_event['suspect']}, confidence: {confidence})"
            )
        
        logger.info(f"Extracted {len(validated_events)} timeline events from document {doc_id}")
        return validated_events
        
    except Exception as e:
        logger.error(f"Error during timeline extraction: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return []


def _parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse timestamp string into datetime object.
    
    Handles various formats:
    - ISO format: "2025-11-12 21:45:00"
    - Date + time: "2025-11-12 21:45"
    - Time only (assumes today): "21:45:00"
    """
    if not timestamp_str:
        return None
    
    timestamp_str = timestamp_str.strip()
    

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%H:%M:%S",
        "%H:%M",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(timestamp_str, fmt)

            if fmt in ["%H:%M:%S", "%H:%M"]:
                today = datetime.now().replace(hour=dt.hour, minute=dt.minute, second=dt.second if dt.second else 0, microsecond=0)
                return today
            return dt
        except ValueError:
            continue
    


    logger.warning(f"Could not parse timestamp format: {timestamp_str}")
    return None

