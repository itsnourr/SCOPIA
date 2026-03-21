"""
LLM-based Evidence Relevance Filter

This module provides LLM-based filtering to determine if evidence is relevant
to a criminal investigation. Used at ingestion time to keep the RAG index clean.

Example Usage:
    >>> from app.tools.llm_filter import is_relevant_llm
    >>> 
    >>> # Check if evidence is relevant
    >>> is_relevant = is_relevant_llm("John entered the building at 9:55 PM")
    >>> print(is_relevant)  # True
"""

import logging
from typing import Dict, Any
from config import Config
from app.llm_factory import create_llm


logger = logging.getLogger(__name__)


_llm_filter_failed = False
_llm_filter_failure_count = 0


def get_llm_filter_status() -> Dict[str, Any]:
    """
    Get the current status of LLM filtering.
    
    Returns:
        Dictionary with:
            - failed: bool - Whether LLM filtering has failed
            - failure_count: int - Number of failures encountered
            - using_fallback: bool - Whether fallback (no filtering) is active
    """
    global _llm_filter_failed, _llm_filter_failure_count
    return {
        'failed': _llm_filter_failed,
        'failure_count': _llm_filter_failure_count,
        'using_fallback': _llm_filter_failed
    }


def reset_llm_filter_status():
    """Reset LLM filter status tracking (call after showing notification)"""
    global _llm_filter_failed, _llm_filter_failure_count
    _llm_filter_failed = False
    _llm_filter_failure_count = 0


def is_relevant_llm(text: str) -> bool:
    """
    LLM-based relevance filter for ANY evidence type (text, image caption, witness, cctv, reports).
    
    Uses Gemini 2.5 Flash to determine if evidence contains information useful to a criminal investigation.
    This approach understands context and relevance even when exact keywords are missing.
    
    Useful evidence includes:
      - Timeline details (times, hours, timestamps)
      - Locations (street, building, apartment, parking, bar, restaurant)
      - People present (witnesses, suspects, victims)
      - Actions/behavior (entered, exited, arguing, shouting)
      - Threats, arguments, conflict
      - Vehicles (sedan, truck, car, license plate)
      - Crime events (murder, assault, weapon, blood)
      - Context leading to or following an incident
    
    Args:
        text: Evidence text to check (can be document content or image caption)
        
    Returns:
        True if evidence is relevant to investigation, False otherwise.
        Falls back to True (keep evidence) if LLM call fails.
        
    Example:
        >>> is_relevant_llm("John entered the building at 9:55 PM")
        True
        >>> is_relevant_llm("Red sedan parked near building")
        True
        >>> is_relevant_llm("Random person walking in mall")
        False
        >>> is_relevant_llm("Outdoor building with statues")
        False
    """
    global _llm_filter_failed, _llm_filter_failure_count
    
    if not text or not text.strip():
        return False
    

    text_truncated = text[:2000] if len(text) > 2000 else text
    
    prompt = f"""You are a forensic evidence relevance classifier.

ETHICAL USE & RESPONSIBILITY:
- This system is for legitimate law enforcement and forensic investigation purposes only
- Classify evidence objectively based on relevance criteria
- Do not bias classification based on protected characteristics
- Maintain professional standards and ethical conduct at all times

Return ONLY one word: "yes" or "no".



You will be given a document (text or an image caption).

It is ONLY relevant to a murder investigation if it contains:



1. A specific person, vehicle, or identifiable object

AND

2. A specific action, movement, behavior, or state

   (entering, exiting, arriving, leaving, walking, arguing,

    fleeing, following, being present or absent)

AND

3. A connection to time, timeline clues, or a location tied

   to the investigation (timestamps, hours, directions of travel,

   proximity to crime scene, being somewhere at a specific time)



If ANY of these three requirements are missing →

mark the document as NOT relevant.



Examples of NOT relevant:

- generic scenery (streets, buildings, sidewalks)

- random people with no time or context

- vehicles with no timeline or behavior

- descriptions with no action or link to the case

- evidence that does not help determine presence/absence

- anything that does NOT reduce or confirm suspicion



Be extremely strict.

If you are not 100% sure → return "no".



Document to evaluate:

\"\"\"{text_truncated}\"\"\"



Return ONLY "yes" or "no".

"""
    
    try:

        logger.warning(f"🔥 LLM relevance check executed for doc: {text_truncated[:60]}...")
        
        if not Config.GEMINI_API_KEY and not Config.OPENAI_API_KEY:
            _llm_filter_failed = True
            _llm_filter_failure_count += 1
            logger.warning("⚠️ LLM relevance check failed: No API key configured; keeping document by fallback (no filtering applied)")
            return True
        
        llm = create_llm(temperature=0.1)
        
        response = llm.invoke(prompt)
        answer = response.content.strip().lower()
        

        is_relevant = "yes" in answer
        
        logger.info(f"✅ LLM response: '{answer}' → relevant: {is_relevant} (text preview: {text_truncated[:100]}...)")
        return is_relevant
        
    except Exception as e:
        _llm_filter_failed = True
        _llm_filter_failure_count += 1
        logger.warning(f"⚠️ LLM relevance check failed: {e}; keeping document by fallback (no filtering applied)")
        return True

