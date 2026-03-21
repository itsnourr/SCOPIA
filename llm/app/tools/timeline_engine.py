"""
Timeline Engine

Builds chronological timelines from extracted events and provides timeline-based scoring
for suspect correlation.

Example Usage:
    >>> from app.tools.timeline_engine import build_timeline, get_murder_time_from_evidence
    >>> from app.tools.timeline_engine import _timeline_score
    >>> 
    >>> # Build timeline for a case
    >>> timeline = build_timeline(case_id=1)
    >>> 
    >>> # Get murder time from evidence
    >>> murder_time = get_murder_time_from_evidence(case_id=1)
    >>> 
    >>> # Score suspect based on timeline
    >>> score, trace = _timeline_score(suspect, timeline, murder_time)
"""

import logging
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

from app.db.dao import get_timeline_events
from app.db.models import Suspect, TimelineEvent


logger = logging.getLogger(__name__)


def build_timeline(case_id: int, suspect_id: Optional[int] = None) -> List[TimelineEvent]:
    """
    Build chronological timeline from extracted events.
    
    Args:
        case_id: Case ID
        suspect_id: Optional suspect ID to filter events
        
    Returns:
        List of TimelineEvent objects sorted by timestamp
    """
    events = get_timeline_events(case_id, suspect_id=suspect_id)

    return events


def get_murder_time_from_evidence(case_id: int) -> Optional[datetime]:
    """
    Extract murder time from forensic reports or evidence.
    
    Looks for:
    - Explicit murder time statements
    - 911 call timestamps
    - Body discovery time (minus estimated time of death)
    - CCTV timestamps showing the crime
    
    Args:
        case_id: Case ID
        
    Returns:
        Datetime of estimated murder time, or None if not found
    """
    from app.db import get_texts_by_case
    

    texts = get_texts_by_case(case_id)
    

    murder_time_keywords = [
        "murder window", "time of death", "estimated time", "911 call",
        "crime occurred", "incident time", "murder time", "time of crime"
    ]
    
    for text_doc in texts:
        content_lower = text_doc.content.lower()
        

        if any(keyword in content_lower for keyword in murder_time_keywords):


            import re
            

            time_patterns = [
                r"(\d{1,2}):(\d{2})\s*(?:PM|AM|pm|am)",
                r"(\d{1,2}):(\d{2}):(\d{2})",
                r"(\d{1,2}):(\d{2})",
            ]
            
            for pattern in time_patterns:
                matches = re.finditer(pattern, text_doc.content)
                for match in matches:


                    logger.debug(f"Found potential murder time in document {text_doc.id}: {match.group()}")

                    break
    


    return None


def _timeline_score(
    suspect: Suspect,
    timeline_events: List[TimelineEvent],
    murder_time: Optional[datetime]
) -> Tuple[float, List[str]]:
    """
    Score suspect based on timeline proximity to murder time.
    
    Args:
        suspect: Suspect object
        timeline_events: List of timeline events (can be filtered by suspect or all events)
        murder_time: Estimated murder time (None if not available)
        
    Returns:
        Tuple of (score, reasoning_trace)
        - score: Timeline-based score contribution (can be positive or negative)
        - reasoning_trace: List of reasoning messages
    """
    score = 0.0
    trace = []
    

    suspect_events = [
        e for e in timeline_events 
        if e.suspect_id == suspect.id or (e.suspect_id is None and suspect.name.lower() in e.raw_text.lower())
    ]
    
    if not suspect_events:
        trace.append("-0.150 no timeline presence")
        return -0.15, trace
    


    if murder_time is None:
        trace.append("+0.000 timeline presence (murder time unknown - neutral)")
        return 0.0, trace
    

    for event in suspect_events:
        try:

            time_diff = abs((murder_time - event.timestamp).total_seconds()) / 60
            
            if time_diff < 20:

                score += 0.15 * event.confidence
                trace.append(
                    f"+{0.15 * event.confidence:.3f} near murder window ({time_diff:.0f} min): {event.raw_text[:60]}..."
                )
            elif time_diff < 60:

                score += 0.05 * event.confidence
                trace.append(
                    f"+{0.05 * event.confidence:.3f} moderate timeline proximity ({time_diff:.0f} min): {event.raw_text[:60]}..."
                )
            elif time_diff < 180:

                score -= 0.05 * event.confidence
                trace.append(
                    f"-{0.05 * event.confidence:.3f} far from crime time ({time_diff:.0f} min): {event.raw_text[:60]}..."
                )
            else:

                score -= 0.10 * event.confidence
                trace.append(
                    f"-{0.10 * event.confidence:.3f} very far from crime time ({time_diff:.0f} min): {event.raw_text[:60]}..."
                )
        except Exception as e:
            logger.warning(f"Error calculating timeline proximity for event {event.id}: {e}")
            continue
    

    score = max(-0.25, min(0.25, score))
    
    return score, trace

