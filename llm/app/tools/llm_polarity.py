"""
LLM-based Polarity Classifier for Decisive Evidence

This module provides a lightweight LLM classifier to determine the polarity
(positive, negative, or neutral) of decisive evidence sentences.

The classifier is used ONLY for sentences that contain both:
- A suspect name
- A decisive forensic term (weapon, DNA, CCTV, etc.)

This ensures we correctly handle cases like:
- "CCTV shows John Doe entering the building" → positive
- "No CCTV footage of John Doe" → negative
- "The CCTV system was installed last year" (with John Doe mentioned elsewhere) → neutral

Example Usage:
    >>> from app.tools.llm_polarity import classify_decisive_polarity
    >>> 
    >>> # Classify a decisive evidence sentence
    >>> polarity = classify_decisive_polarity(
    ...     sentence="CCTV shows John Doe entering the building at 10:05 PM",
    ...     suspect_name="John Doe",
    ...     term="cctv"
    ... )
    >>> print(polarity)  # "positive"
"""

import logging
from typing import Literal

from app.llm_factory import create_llm

from config import Config
from app.db.dao import get_cached_polarity, save_polarity_cache


logger = logging.getLogger(__name__)


Polarity = Literal["positive", "negative", "neutral"]


def classify_decisive_polarity(sentence: str, suspect_name: str, term: str) -> Polarity:
    """
    Classify the polarity of a decisive evidence sentence using a lightweight LLM call.
    
    This function is called ONLY for sentences that contain both:
    - The suspect name (token-wise match)
    - A decisive forensic term (weapon, DNA, CCTV, etc.)
    
    Args:
        sentence: The sentence containing both suspect name and decisive term
        suspect_name: Name of the suspect
        term: The decisive term found in the sentence
        
    Returns:
        "positive", "negative", or "neutral"
        
        - positive: Sentence supports suspect involvement (e.g., presence at scene, handling weapon)
        - negative: Sentence supports suspect was NOT involved (e.g., alibi, absence from footage)
        - neutral: Sentence mentions suspect/term but doesn't clearly support or exclude involvement
        
    Example:
        >>> classify_decisive_polarity(
        ...     "CCTV shows John Doe entering the building at 10:05 PM",
        ...     "John Doe",
        ...     "cctv"
        ... )
        'positive'
        
        >>> classify_decisive_polarity(
        ...     "No CCTV footage of John Doe entering or leaving the building",
        ...     "John Doe",
        ...     "cctv"
        ... )
        'negative'
        
        >>> classify_decisive_polarity(
        ...     "The CCTV system was installed last year by John Doe's company",
        ...     "John Doe",
        ...     "cctv"
        ... )
        'neutral'
    """

    cached_polarity = get_cached_polarity(suspect_name, term, sentence)
    if cached_polarity:
        logger.debug(
            f"✅ Cache hit: polarity='{cached_polarity}' for suspect='{suspect_name}', "
            f"term='{term}', sentence='{sentence[:60]}...'"
        )
        return cached_polarity
    

    if not Config.GEMINI_API_KEY and not Config.OPENAI_API_KEY:
        logger.warning(
            "No API key configured; defaulting to 'neutral' for decisive evidence polarity"
        )
        polarity = "neutral"
    else:

        prompt = f"""You are a forensic evidence polarity classifier.

ETHICAL USE & RESPONSIBILITY:
- This system is for legitimate law enforcement and forensic investigation purposes only
- Classify evidence polarity objectively based on factual statements
- Do not bias classification based on protected characteristics
- Maintain professional standards and ethical conduct at all times
- All analysis is decision support only, not a legal conclusion

Given a sentence involving a suspect and a decisive term (like CCTV, fingerprints, DNA, weapon, prints, etc.), determine whether the sentence provides POSITIVE, NEGATIVE, or NEUTRAL evidence about the suspect's involvement in the crime.

Rules:

POSITIVE evidence:
- Confirms presence near or at time of crime
- Confirms contact with weapon, fingerprints match, DNA match
- Confirms behavior consistent with involvement
- Confirms appearance on CCTV DURING the murder window

NEGATIVE evidence:
- Confirms absence during the crime (left earlier, was elsewhere, alibi confirmed)
- Confirms NO CCTV footage of suspect during critical time
- Confirms fingerprints NOT found
- Confirms DNA NOT found
- Confirms suspect was far away from crime scene
- Confirms contradictory evidence supporting innocence

NEUTRAL evidence:
- Not clearly related to involvement or absence
- Mentions the suspect but does not confirm presence or absence
- CCTV about unrelated time or unrelated subject

Return EXACTLY one word:
positive / negative / neutral.

Sentence: "{sentence}"
Suspect: "{suspect_name}"
Decisive Term: "{term}"

Answer:"""

    try:

        llm = create_llm(
            temperature=0.0,
            max_tokens=10
        )
        
        response = llm.invoke(prompt)
        answer = response.content.strip().lower()
        

        answer_word = answer.split()[0] if answer.split() else ""
        

        if answer_word in ("positive", "negative", "neutral"):
            polarity = answer_word
            logger.debug(
                f"✅ Polarity classification: '{answer_word}' for sentence: '{sentence[:80]}...' "
                f"(suspect: {suspect_name}, term: {term})"
            )
        else:
            logger.warning(
                f"⚠️ Invalid polarity response '{answer}' (expected 'positive', 'negative', or 'neutral'); "
                f"defaulting to 'neutral' for sentence: '{sentence[:80]}...'"
            )
            polarity = "neutral"
            
    except Exception as e:
        logger.warning(
            f"⚠️ Error classifying polarity for sentence '{sentence[:80]}...': {e}; "
            f"defaulting to 'neutral'"
        )
        polarity = "neutral"
    

    save_polarity_cache(suspect_name, term, sentence, polarity)
    
    return polarity

