"""
Evidence Correlator Tool for Forensic Crime Analysis Agent

This tool ranks suspects by how well case evidence supports them using advanced hybrid scoring:

Core Scoring:
- Vector similarity (semantic matching with source-type weighting)
- Keyword matching (name mentions, decisive terms, metadata)
- Rule-based boosts (forensic evidence like DNA, fingerprints)

Advanced Features:
- Source-type weighting (forensic > image > report > witness)
- Polarity-aware decisive evidence classification (LLM-based)
  - Sentences with suspect name + decisive terms are classified as positive/negative/neutral
  - Correctly handles cases like "No CCTV footage of John Doe" (negative) vs "CCTV shows John Doe" (positive)
  - Uses lightweight LLM classifier for accurate polarity detection
- Metadata reasoning (vehicle + location = strong signal)
- Evidence coherence (consistency between evidence documents)
- Vision AI cross-checking (vehicle, clothing, object matches)
- Location triangulation (workplace, neighborhood matches)
- Cross-evidence graph reasoning (weighted connection counting)
- Rare clue weighting (confession, DNA get extra weight)
- Improved contradiction detection (vehicle type/color mismatches)
- Negative evidence handling (suspect not mentioned, weak evidence decay)
- Reasoning Trace (Explainable AI): Full forensic justification for each score

The scoring is mostly deterministic (with narrow LLM decision surface for polarity classification),
transparent, normalized to [0, 1.0], and includes detailed rationale with a complete reasoning
trace showing how each score component was calculated, including polarity classifications.

Example Usage:
    >>> from app.tools.evidence_correlator import correlate_and_persist
    >>> 
    >>> # Correlate evidence with suspects
    >>> result = correlate_and_persist(case_id=1, query="Who is most likely responsible?")
    >>> 
    >>> # View rankings
    >>> for r in result["ranked"]:
    ...     print(f"{r['suspect_name']}: {r['score']:.2f}")
    ...     print(f"  Clues: {r['matched_clues']}")
    ...     print(f"  Reasoning Trace:")
    ...     for line in r.get('reasoning_trace', []):
    ...         print(f"    • {line}")
    
Integration Hook:
    After RAG rebuild or adding new evidence:
    
    >>> from app.tools.evidence_correlator import correlate_and_persist
    >>> from app.rag import build_case_index
    >>> 
    >>> # Rebuild RAG index
    >>> build_case_index(case_id=1)
    >>> 
    >>> # Correlate evidence with suspects
    >>> result = correlate_and_persist(case_id=1, query="most incriminating evidence")
    >>> 
    >>> # Visualize in Streamlit
    >>> import streamlit as st
    >>> for suspect in result['ranked']:
    ...     st.metric(suspect['suspect_name'], f"{suspect['score']:.2f}")
    ...     st.write(f"Clues: {', '.join(suspect['matched_clues'])}")
"""

import re
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter, defaultdict

from sentence_transformers import SentenceTransformer

from app.rag import query_documents, get_case_index_status
from app.db import get_suspects_by_case, get_case
from app.db.dao import save_analysis_results
from app.tools.llm_filter import get_llm_filter_status, reset_llm_filter_status
from app.tools.llm_polarity import classify_decisive_polarity
from app.tools.timeline_engine import build_timeline, get_murder_time_from_evidence, _timeline_score
from app.tools.contradiction_graph import (
    build_contradiction_graph,
    detect_contradictions,
    add_contradiction_edges,
    _contradiction_penalty
)


logger = logging.getLogger(__name__)
logging.getLogger("app.tools.evidence_correlator").setLevel(logging.DEBUG)






W_SIM = 0.35
W_KW = 0.30
W_DECISIVE = 0.35


POSITIVE_DECISIVE_WEIGHT = 0.15
NEGATIVE_DECISIVE_WEIGHT = 0.12

DECISIVE_HIT_VALUE = POSITIVE_DECISIVE_WEIGHT


WEIGHTS_BY_SOURCE = {
    "forensic": 1.0,
    "image": 0.8,
    "report": 0.7,
    "witness": 0.5,
    "note": 0.6,
    "statement": 0.5,
    "suspect": 0.4,
    "unknown": 0.4
}


DECISIVE_PROXIMITY_TOKENS = 5


DEFAULT_QUERY = "most incriminating evidence, presence at scene, motive, timeline, witnesses"



DECISIVE_CATEGORIES = {
    "weapon": {
        "knife", "gun", "firearm", "weapon", "blade", "pistol", "rifle", "machete"
    },
    "bio": {
        "dna", "blood", "fingerprint", "fingerprints", "prints", "hair", "saliva"
    },
    "video": {
        "cctv", "camera", "footage", "video", "security camera", "recording"
    },
    "trace": {
        "fibers", "residue", "gunshot residue", "g.s.r.", "powder residue", "mud", "soil"
    },
    "statement": {
        "confessed", "confession", "admitted", "admission", "statement"
    },
    "location": {
        "entered", "exited", "arrived", "left", "present at", "near the scene",
        "at the scene", "in the apartment", "in the building"
    }
}



DECISIVE_TERMS = {term for category in DECISIVE_CATEGORIES.values() for term in category}


DECISIVE_TERMS.update({
    'threat', 'threatened', 'seen', 'spotted', 'caught'
})




DECISIVE_WEIGHTS = {

    "dna": 0.25,
    "fingerprint": 0.20,
    "fingerprints": 0.20,
    "prints": 0.20,
    

    "weapon": 0.20,
    "knife": 0.20,
    "gun": 0.20,
    "firearm": 0.20,
    "blade": 0.20,
    "pistol": 0.20,
    "rifle": 0.20,
    "machete": 0.20,
    

    "cctv": 0.15,
    "footage": 0.15,
    "camera": 0.15,
    "video": 0.15,
    "security camera": 0.15,
    "recording": 0.15,
    

    "shoeprint": 0.10,
    "footprint": 0.10,
    "tire tracks": 0.10,
    "fibers": 0.10,
    "residue": 0.10,
    "gunshot residue": 0.10,
    "g.s.r.": 0.10,
    "powder residue": 0.10,
    "mud": 0.10,
    "soil": 0.10,
    

    "confession": 0.20,
    "confessed": 0.20,
    "admitted": 0.20,
    "admission": 0.20,
    

    "entered": 0.15,
    "exited": 0.15,
    "arrived": 0.15,
    "left": 0.15,
    "present at": 0.15,
    "at the scene": 0.15,
    

    "threat": 0.15,
    "threatened": 0.15,
    "seen": 0.10,
    "spotted": 0.10,
    "caught": 0.15,
    "blood": 0.20,
    "hair": 0.15,
    "saliva": 0.20,
}


DEFAULT_DECISIVE_WEIGHT = 0.10


RARE_TERMS = {
    'confession': 0.20,
    'admitted': 0.15,
    'dna': 0.15,
    'fingerprints': 0.10,
    'caught': 0.10,
    'video': 0.08,
    'cctv': 0.08
}


VEHICLE_TYPES = ['sedan', 'truck', 'motorcycle', 'van', 'suv', 'car', 'bike', 'bicycle', 'pickup']


COLOR_WORDS = ['red', 'blue', 'black', 'white', 'green', 'yellow', 'silver', 'gray', 'grey', 
               'brown', 'orange', 'purple', 'pink', 'beige', 'tan']


np.random.seed(42)


_embedding_model: Optional[SentenceTransformer] = None


def _get_embedding_model() -> SentenceTransformer:
    """
    Get or create embedding model (singleton pattern)
    Uses same model as RAG for consistency
    
    Returns:
        SentenceTransformer model
    """
    global _embedding_model
    
    if _embedding_model is None:
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        _embedding_model.eval()
        logger.info("✅ Embedding model loaded")
    
    return _embedding_model


def extract_evidence_context(
    case_id: int,
    query: Optional[str] = None,
    k: int = 8
) -> List[Dict[str, Any]]:
    """
    Use RAG to fetch top-k most relevant documents for case
    
    Args:
        case_id: Case ID to retrieve evidence for
        query: Search query (if None, uses DEFAULT_QUERY)
        k: Number of documents to retrieve
        
    Returns:
        List of evidence documents, each containing:
            - doc_id: Document identifier
            - title: Document title (may be None)
            - text: Document content
            - source_type: Type of evidence (witness, report, image, etc.)
            - score: Relevance score from RAG
            
    Example:
        >>> docs = extract_evidence_context(case_id=1, k=5)
        >>> for doc in docs:
        ...     print(f"{doc['source_type']}: {doc['text'][:50]}")
    """
    logger.info(f"📚 Extracting evidence context for case {case_id}")
    

    if query is None:
        query = DEFAULT_QUERY
        logger.debug(f"Using default query: {query}")
    

    status = get_case_index_status(case_id)
    if not status.get('indexed') or status.get('document_count', 0) == 0:
        logger.warning(f"Case {case_id} has no indexed evidence")
        return []
    

    results = query_documents(query=query, case_id=case_id, k=k)
    





    evidence_docs = []
    for result in results:
        source_type = result['metadata'].get('source_type', 'unknown')
        

        if source_type == 'suspect':
            logger.debug(f"Skipping suspect profile: {result['metadata'].get('title')}")
            continue
        


        

        doc = {
            'doc_id': result['metadata'].get('doc_id', 'unknown'),
            'title': result['metadata'].get('title'),
            'text': result['text'],
            'source_type': source_type,
            'score': result['score']
        }
        evidence_docs.append(doc)
    
    logger.info(f"✅ Retrieved {len(evidence_docs)} evidence documents (suspect profiles filtered out, irrelevant evidence already filtered at ingestion)")
    
    return evidence_docs


def _extract_vehicle_info(text: str) -> Dict[str, Any]:
    """
    Extract vehicle color and type from text
    
    Returns:
        {'color': str or None, 'type': str or None}
    """
    text_lower = text.lower()
    color = None
    vehicle_type = None
    

    for c in COLOR_WORDS:
        if c in text_lower:
            color = c
            break
    

    for vt in VEHICLE_TYPES:
        if vt in text_lower:
            vehicle_type = vt
            break
    
    return {'color': color, 'type': vehicle_type}


def _detect_vehicle_contradictions(
    evidence_texts: List[str],
    suspect_vehicle_terms: List[str],
    metadata: Dict[str, Any]
) -> float:
    """
    Detect vehicle contradictions between evidence and suspect metadata
    
    Returns:
        Penalty score (0.0 to 0.15)
    """
    if not suspect_vehicle_terms:
        return 0.0
    
    penalty = 0.0
    

    suspect_vehicle_str = " ".join(suspect_vehicle_terms).lower()
    suspect_info = _extract_vehicle_info(suspect_vehicle_str)
    

    for text in evidence_texts:
        evidence_info = _extract_vehicle_info(text)
        

        if evidence_info['type'] and suspect_info['type']:
            if evidence_info['type'] != suspect_info['type']:
                penalty += 0.15
                logger.debug(f"Vehicle type mismatch: evidence={evidence_info['type']}, suspect={suspect_info['type']}")
        

        if evidence_info['color'] and suspect_info['color']:
            if evidence_info['color'] != suspect_info['color']:
                penalty += 0.10
                logger.debug(f"Vehicle color mismatch: evidence={evidence_info['color']}, suspect={suspect_info['color']}")
    
    return min(penalty, 0.15)


def _vision_ai_crosscheck(
    evidence_docs: List[Dict[str, Any]],
    suspect_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[float, List[str]]:
    """
    Cross-check Vision AI captions with suspect metadata
    
    Checks for:
    - Vehicle matches (color, type)
    - Clothing matches
    - Object matches
    - Appearance descriptors
    
    Returns:
        Tuple of (boost score [0, 0.15], list of match descriptions)
    """
    if not metadata:
        return (0.0, [])
    
    boost = 0.0
    match_descriptions = []
    vehicle_terms = []
    

    if 'vehicle' in metadata or 'vehicles' in metadata or 'known_vehicles' in metadata:
        vehicle_value = metadata.get('vehicle') or metadata.get('vehicles') or metadata.get('known_vehicles')
        if isinstance(vehicle_value, list):
            vehicle_terms = [str(v).lower() for v in vehicle_value]
        elif vehicle_value:
            vehicle_terms = [str(vehicle_value).lower()]
    

    for doc in evidence_docs:
        if doc.get('source_type') == 'image':
            caption = doc.get('text', '').lower()
            

            if vehicle_terms:
                for vehicle_term in vehicle_terms:
                    if vehicle_term in caption:
                        boost += 0.10
                        match_descriptions.append(f"Vision AI vehicle match: {vehicle_term}")
                        logger.debug(f"Vision AI vehicle match: {vehicle_term} in caption")
                        break
            

            if 'clothing' in metadata or 'appearance' in metadata:
                clothing_value = metadata.get('clothing') or metadata.get('appearance')
                if clothing_value:
                    clothing_str = str(clothing_value).lower()
                    if clothing_str in caption:
                        boost += 0.08
                        match_descriptions.append(f"Vision AI clothing match: {clothing_str}")
                        logger.debug(f"Vision AI clothing match: {clothing_str} in caption")
            

            object_keywords = ['weapon', 'gun', 'knife', 'bag', 'backpack', 'tool']
            for keyword in object_keywords:
                if keyword in caption and keyword in str(metadata).lower():
                    boost += 0.05
                    match_descriptions.append(f"Vision AI object match: {keyword}")
                    break
    
    return (min(boost, 0.15), match_descriptions)


def _parse_time_to_minutes(value: Any) -> Optional[int]:
    """
    Parse a time like '22:30', '10:30 pm', or a datetime/time object
    into minutes from midnight. Returns None if cannot parse.
    
    Args:
        value: Time value (string, datetime, time, or int/float)
        
    Returns:
        Minutes from midnight (0-1439) or None if cannot parse
        
    Example:
        >>> _parse_time_to_minutes("22:30")
        1350
        >>> _parse_time_to_minutes("10:30 PM")
        1350
    """
    if value is None:
        return None
    

    if isinstance(value, (int, float)):
        return int(value)
    

    try:
        import datetime as _dt
        if isinstance(value, (_dt.datetime, _dt.time)):
            return value.hour * 60 + value.minute
    except Exception:
        pass
    

    s = str(value).strip().lower()
    

    m = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', s)
    if not m:
        return None
    
    hour = int(m.group(1))
    minute = int(m.group(2))
    ampm = m.group(3)
    
    if ampm == 'pm' and hour < 12:
        hour += 12
    if ampm == 'am' and hour == 12:
        hour = 0
    
    return hour * 60 + minute


def _timeline_consistency(
    evidence_docs: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> float:
    """
    Check timeline consistency between evidence and suspect alibi.
    
    Uses:
      - last_seen_time / alibi_time in suspect metadata (if present)
      - HH:MM patterns in evidence texts (very approximate)
    
    Returns:
        Boost/penalty score in range [-0.10, 0.15]
    """
    if not metadata:
        return 0.0
    
    last_seen_time = _parse_time_to_minutes(metadata.get('last_seen_time'))
    alibi_time = _parse_time_to_minutes(metadata.get('alibi_time'))
    

    if last_seen_time is None and alibi_time is None:
        return 0.0
    

    evidence_times: List[int] = []
    for doc in evidence_docs:
        text = doc.get('text', '') or ''
        for match in re.findall(r'\d{1,2}:\d{2}\s*(?:am|pm)?', text, flags=re.IGNORECASE):
            t = _parse_time_to_minutes(match)
            if t is not None:
                evidence_times.append(t)
    
    if not evidence_times:
        return 0.0
    

    evidence_times.sort()
    ev_time = evidence_times[len(evidence_times) // 2]
    
    boost = 0.0
    

    if last_seen_time is not None:
        diff = abs(ev_time - last_seen_time)
        if diff <= 60:
            boost += 0.08
        elif diff <= 120:
            boost += 0.03
    

    if alibi_time is not None:
        diff_alibi = abs(ev_time - alibi_time)

        alibi_confirmed = metadata.get('alibi_confirmed', False) or metadata.get('alibi_verified', False)
        
        if diff_alibi > 180:
            penalty = 0.30 if not alibi_confirmed else 0.40
            boost -= penalty
        elif diff_alibi > 120:
            penalty = 0.20 if not alibi_confirmed else 0.30
            boost -= penalty
        elif diff_alibi > 60:
            penalty = 0.10 if not alibi_confirmed else 0.20
            boost -= penalty
    

    if metadata.get('alibi_confirmed', False) or metadata.get('alibi_verified', False):
        if alibi_time is not None:
            diff_alibi = abs(ev_time - alibi_time)
            if diff_alibi > 60:
                boost -= 0.15
    

    result = max(-0.50, min(0.15, boost))
    if result != 0.0:
        logger.debug(f"Timeline consistency: ev_time={ev_time//60}:{ev_time%60:02d}, last_seen={last_seen_time//60 if last_seen_time else None}:{last_seen_time%60:02d if last_seen_time else None}, alibi={alibi_time//60 if alibi_time else None}:{alibi_time%60:02d if alibi_time else None}, boost={result:.3f}")
    
    return result


def _location_triangulation(
    evidence_texts: List[str],
    metadata: Optional[Dict[str, Any]] = None
) -> float:
    """
    Check if evidence mentions suspect's known locations
    
    Returns:
        Boost score [0, 0.15]
    """
    if not metadata:
        return 0.0
    
    boost = 0.0
    location_terms = []
    

    location_keys = ['workplace', 'neighborhood', 'address', 'known_locations', 'residence']
    for key in location_keys:
        if key in metadata:
            value = metadata[key]
            if isinstance(value, list):
                location_terms.extend([str(loc).lower() for loc in value])
            elif value:
                location_terms.append(str(value).lower())
    

    for text in evidence_texts:
        text_lower = text.lower()
        for loc_term in location_terms:
            if loc_term in text_lower:
                boost += 0.10
                logger.debug(f"Location match: {loc_term} in evidence")
                break
    
    return min(boost, 0.15)


def _cross_evidence_graph(
    evidence_docs: List[Dict[str, Any]],
    suspect_name: str,
    extra_terms: List[str],
    decisive_hits: List[str]
) -> float:
    """
    Build weighted graph of evidence connections to suspect
    
    Counts weighted evidence documents that connect to suspect via:
    - Name mention (weight = 1.0)
    - Metadata terms (weight = 0.7)
    - Decisive evidence (weight = 1.3)
    
    Returns:
        Graph score [0, 0.15]
    """
    weighted_score = 0.0
    name_tokens = _tokenize(suspect_name)
    

    WEIGHT_NAME = 1.0
    WEIGHT_METADATA = 0.7
    WEIGHT_DECISIVE = 1.3
    
    for doc in evidence_docs:
        text = doc.get('text', '').lower()
        text_tokens = _tokenize(text)
        

        if any(token in text_tokens for token in name_tokens):
            weighted_score += WEIGHT_NAME
            continue
        

        if extra_terms:
            extra_tokens = set()
            for term in extra_terms:
                extra_tokens.update(_tokenize(term))
            if any(token in text_tokens for token in extra_tokens):
                weighted_score += WEIGHT_METADATA
                continue
        

        if decisive_hits:
            for hit in decisive_hits:
                if hit in text_tokens:
                    weighted_score += WEIGHT_DECISIVE
                    break
    




    max_possible = len(evidence_docs) * WEIGHT_DECISIVE
    if max_possible > 0:
        graph_score = min((weighted_score / max_possible) * 0.15, 0.15)
    else:
        graph_score = 0.0
    
    logger.debug(f"Cross-evidence graph: weighted_score={weighted_score:.2f} → graph_score={graph_score:.3f}")
    
    return graph_score


def _split_sentences(text: str) -> List[str]:
    """
    Rough sentence splitter for proximity logic.
    Splits on ., !, ?, and newlines.
    
    Args:
        text: Text to split into sentences
        
    Returns:
        List of sentence strings (stripped, non-empty)
        
    Example:
        >>> _split_sentences("John's fingerprints found. Jane was seen. End.")
        ["John's fingerprints found", "Jane was seen", "End"]
    """

    text = text.replace('\r', '\n')
    

    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    

    return [s.strip() for s in sentences if s.strip()]


def _tokenize(text: str) -> Set[str]:
    """
    Simple tokenization for keyword matching
    
    Args:
        text: Text to tokenize
        
    Returns:
        Set of lowercase tokens
        
    Example:
        >>> _tokenize("John's fingerprints were found!")
        {'john', 'fingerprints', 'were', 'found'}
    """

    text = text.lower()
    

    text = re.sub(r'[^\w\s]', ' ', text)
    

    tokens = set(text.split())
    
    return tokens


def _find_decisive_sentences(text: str, suspect_name: str) -> List[Tuple[str, str]]:
    """
    Find sentences that contain both the suspect name and at least one decisive term.
    
    This function identifies sentences that need polarity classification because they
    contain both a suspect mention and a decisive forensic term. The sentence is
    returned along with the decisive term found in it.
    
    Args:
        text: The evidence text to search
        suspect_name: Name of the suspect to search for
        
    Returns:
        List of tuples (sentence, decisive_term) where:
        - sentence: The full sentence containing both suspect name and decisive term
        - decisive_term: The decisive term found in the sentence
        
    Example:
        >>> text = "CCTV shows John Doe entering the building. No footage of Jane Smith."
        >>> _find_decisive_sentences(text, "John Doe")
        [("CCTV shows John Doe entering the building.", "cctv")]
        
        >>> _find_decisive_sentences(text, "Jane Smith")
        [("No footage of Jane Smith.", "footage")]
    """

    name_tokens = _tokenize(suspect_name)
    

    sentences = _split_sentences(text)
    
    results = []
    
    for sent in sentences:

        if len(sent.strip()) < 10:
            continue
        
        sent_lower = sent.lower()
        sent_tokens = _tokenize(sent)
        

        has_suspect = any(token in sent_tokens for token in name_tokens)
        if not has_suspect:
            continue
        

        found_term = None
        for term in DECISIVE_TERMS:

            if term in sent_lower:

                term_found = False
                for token in sent_tokens:
                    if term in token or token in term:
                        term_found = True
                        break
                
                if term_found:
                    found_term = term
                    break
        

        if found_term:
            results.append((sent.strip(), found_term))
    
    return results


def _keyword_features(
    evidence_texts: List[str],
    suspect_name: str,
    extra_terms: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compute keyword-based features from evidence with metadata reasoning
    
    Args:
        evidence_texts: List of evidence text strings
        suspect_name: Suspect's name to search for
        extra_terms: Additional terms to search (vehicle, location, etc.)
        metadata: Optional suspect metadata dict for enhanced reasoning
        
    Returns:
        Dictionary with:
            - name_hits: Number of times suspect name appears
            - term_hits: Number of extra term matches
            - decisive_hits: List of decisive forensic terms found
            - keyword_score: Normalized keyword score [0, 1] (includes metadata boosts)
            
    Example:
        >>> texts = ["John's fingerprints found", "John seen at scene"]
        >>> metadata = {"vehicle": "red sedan", "workplace": "bank"}
        >>> features = _keyword_features(texts, "John", ["fingerprints"], metadata)
        >>> features['name_hits']
        2
        >>> features['decisive_hits']
        ['fingerprints']
    """

    all_tokens = set()
    for text in evidence_texts:
        all_tokens.update(_tokenize(text))
    

    name_tokens = _tokenize(suspect_name)
    name_hits = 0
    evidence_with_suspect = []
    
    for text in evidence_texts:
        text_tokens = _tokenize(text)
        if any(token in text_tokens for token in name_tokens):
            name_hits += 1
            evidence_with_suspect.append(text)
    

    term_hits = 0
    if extra_terms:
        extra_tokens = set()
        for term in extra_terms:
            extra_tokens.update(_tokenize(term))
        

        if evidence_with_suspect:
            for text in evidence_with_suspect:
                sentences = _split_sentences(text)
                for sent in sentences:
                    sent_tokens = _tokenize(sent)

                    if any(t in sent_tokens for t in name_tokens):

                        for token in extra_tokens:
                            if token in sent_tokens:
                                term_hits += 1

        else:

            for text in evidence_texts:
                sentences = _split_sentences(text)
                for sent in sentences:
                    sent_tokens = _tokenize(sent)

                    has_metadata = any(t in sent_tokens for t in extra_tokens)
                    has_decisive = any(term in sent.lower() for term in DECISIVE_TERMS)
                    if has_metadata and has_decisive:
                        for token in extra_tokens:
                            if token in sent_tokens:
                                term_hits += 1
    




    decisive_hit_set = set()
    
    if evidence_with_suspect:
        logger.debug(f"Suspect '{suspect_name}' mentioned in {len(evidence_with_suspect)} evidence document(s)")
        

        for text in evidence_with_suspect:

            sentences = _split_sentences(text)
            
            for sent in sentences:
                sent_lower = sent.lower()
                sent_tokens = _tokenize(sent)
                

                if not any(t in sent_tokens for t in name_tokens):
                    continue
                

                for term in DECISIVE_TERMS:

                    if term in sent_lower:


                        term_found = False
                        for token in sent_tokens:
                            if term in token or token in term:
                                term_found = True
                                break
                        
                        if term_found:
                            decisive_hit_set.add(term)
                            logger.debug(
                                f"  ✅ Decisive term '{term}' linked to '{suspect_name}' "
                                f"within same sentence: '{sent[:80]}...'"
                            )
    else:



        logger.debug(f"Suspect '{suspect_name}' NOT mentioned in evidence - checking metadata sentence-level proximity only")
        if extra_terms:
            extra_tokens = set()
            for term in extra_terms:
                extra_tokens.update(_tokenize(term))
            

            for text in evidence_texts:

                sentences = _split_sentences(text)
                
                for sent in sentences:
                    sent_lower = sent.lower()
                    sent_tokens = _tokenize(sent)
                    

                    has_metadata = any(t in sent_tokens for t in extra_tokens)
                    if not has_metadata:
                        continue
                    

                    for term in DECISIVE_TERMS:
                        if term in sent_lower:

                            term_found = False
                            for token in sent_tokens:
                                if term in token or token in term:
                                    term_found = True
                                    break
                            
                            if term_found and term not in decisive_hit_set:
                                decisive_hit_set.add(term)
                                logger.debug(f"  ✅ Decisive term '{term}' found in same sentence as metadata for '{suspect_name}'")
    
    decisive_hits = list(decisive_hit_set)
    


    keyword_score = 0.0
    if name_hits > 0:

        keyword_score += min(name_hits * 0.02, 0.25)
    if term_hits > 0:

        keyword_score += min(term_hits * 0.015, 0.3)
    

    if decisive_hits:
        keyword_score += min(len(decisive_hits) * 0.05, 0.2)
    

    metadata_score = 0.0
    negative_evidence_penalty = 0.0
    
    if metadata and extra_terms:

        vehicle_mentioned = False
        vehicle_terms = []
        if 'vehicle' in metadata or 'vehicles' in metadata or 'known_vehicles' in metadata:
            vehicle_value = metadata.get('vehicle') or metadata.get('vehicles') or metadata.get('known_vehicles')
            if isinstance(vehicle_value, list):
                vehicle_terms = [str(v).lower() for v in vehicle_value]
            elif vehicle_value:
                vehicle_terms = [str(vehicle_value).lower()]
        

        for text in evidence_texts:
            text_lower = text.lower()
            for vehicle_term in vehicle_terms:
                if vehicle_term in text_lower:
                    vehicle_mentioned = True


                    break
        

        workplace_mentioned = False
        if 'workplace' in metadata or 'occupation' in metadata:
            workplace_value = metadata.get('workplace') or metadata.get('occupation')
            if workplace_value:
                workplace_str = str(workplace_value).lower()
                for text in evidence_texts:
                    if workplace_str in text.lower():
                        workplace_mentioned = True
                        break
        

        if vehicle_mentioned and workplace_mentioned:
            metadata_score += 0.20
        elif vehicle_mentioned:
            metadata_score += 0.15
        elif workplace_mentioned:
            metadata_score += 0.10
        

        negative_evidence_penalty += _detect_vehicle_contradictions(evidence_texts, vehicle_terms, metadata)
    
    keyword_score += min(metadata_score, 0.2)
    

    location_boost = _location_triangulation(evidence_texts, metadata)
    keyword_score += location_boost
    

    keyword_score = max(0.0, keyword_score - negative_evidence_penalty)
    

    if negative_evidence_penalty > 0:
        contradiction_penalty = min(negative_evidence_penalty * 0.4, 0.10)
        keyword_score = max(0.0, keyword_score - contradiction_penalty)
        logger.debug(f"Contradiction penalty applied: {contradiction_penalty:.3f}")
    
    keyword_score = min(keyword_score, 1.0)
    
    logger.info(
        f"Keyword features for '{suspect_name}': name_hits={name_hits}, term_hits={term_hits}, "
        f"decisive_hits={decisive_hits[:5]}{'...' if len(decisive_hits) > 5 else ''} ({len(decisive_hits)} total), "
        f"score={keyword_score:.3f}"
    )
    
    return {
        'name_hits': name_hits,
        'term_hits': term_hits,
        'decisive_hits': decisive_hits,
        'keyword_score': keyword_score
    }


def _vector_similarity(
    suspect_profile: str,
    evidence_texts: List[str],
    source_types: Optional[List[str]] = None,
    evidence_scores: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Compute vector similarity between suspect and evidence with source weighting
    
    Args:
        suspect_profile: Suspect's profile text
        evidence_texts: List of evidence texts
        source_types: Optional list of source types (forensic, witness, etc.)
        evidence_scores: Optional list of RAG relevance scores (for decay)
        
    Returns:
        Dictionary with:
            - sims: List of similarity scores for each evidence doc
            - base_sim: Base similarity (mean of top-3 weighted sims)
            - coherence: Average similarity between evidence documents
            
    Example:
        >>> profile = "Known burglar with history"
        >>> texts = ["Burglary at jewelry store", "Witness saw suspect"]
        >>> sources = ["report", "witness"]
        >>> sim = _vector_similarity(profile, texts, sources)
        >>> sim['base_sim']
        0.456
    """
    if not evidence_texts:
        return {'sims': [], 'base_sim': 0.0, 'coherence': 0.0}
    

    model = _get_embedding_model()
    

    profile_embedding = model.encode(suspect_profile, convert_to_numpy=True)
    

    evidence_embeddings = model.encode(evidence_texts, convert_to_numpy=True)
    

    sims = []
    for i, evidence_emb in enumerate(evidence_embeddings):

        sim = np.dot(profile_embedding, evidence_emb) / (
            np.linalg.norm(profile_embedding) * np.linalg.norm(evidence_emb)
        )
        

        if source_types and i < len(source_types):
            source_type = source_types[i].lower() if isinstance(source_types[i], str) else "unknown"
            weight = WEIGHTS_BY_SOURCE.get(source_type, WEIGHTS_BY_SOURCE["unknown"])
            sim = sim * weight
        

        if evidence_scores and i < len(evidence_scores):
            rag_score = evidence_scores[i]
            if rag_score < 0.3:
                decay_factor = max(0.5, rag_score / 0.3)
                sim = sim * decay_factor
        
        sims.append(float(sim))
    

    if len(sims) >= 3:
        top_sims = sorted(sims, reverse=True)[:3]
        base_sim = float(np.mean(top_sims))
    else:
        base_sim = float(np.mean(sims)) if sims else 0.0
    

    coherence = 0.0
    if len(evidence_embeddings) > 1:
        coherence_sims = []
        for i in range(len(evidence_embeddings)):
            for j in range(i + 1, len(evidence_embeddings)):
                coh_sim = np.dot(evidence_embeddings[i], evidence_embeddings[j]) / (
                    np.linalg.norm(evidence_embeddings[i]) * np.linalg.norm(evidence_embeddings[j])
                )
                coherence_sims.append(float(coh_sim))
        coherence = float(np.mean(coherence_sims)) if coherence_sims else 0.0
    
    logger.debug(f"Vector similarity: base_sim={base_sim:.3f}, coherence={coherence:.3f}, docs={len(sims)}")
    
    return {
        'sims': sims,
        'base_sim': base_sim,
        'coherence': coherence
    }


def _hybrid_score(
    base_sim: float,
    keyword_score: float,
    decisive_hits: List[str],
    coherence: float = 0.0,
    has_name_match: bool = True
) -> float:
    """
    Combine signals into final hybrid score with coherence and negative evidence handling
    
    Args:
        base_sim: Vector similarity score [0, 1]
        keyword_score: Keyword matching score [0, 1]
        decisive_hits: List of decisive forensic terms
        coherence: Evidence coherence score [0, 1] (similarity between evidence docs)
        has_name_match: Whether suspect name appears in evidence
        
    Returns:
        Final hybrid score [0, 1]
        
    Example:
        >>> score = _hybrid_score(0.7, 0.5, ['fingerprints', 'dna'], coherence=0.8, has_name_match=True)
        >>> score
        0.805  # 0.50*0.7 + 0.25*0.5 + 0.25 (capped) + coherence boost
    """


    decisive_bonus = 0.0
    for hit in decisive_hits:
        if hit in RARE_TERMS:
            decisive_bonus += RARE_TERMS[hit]
        else:
            decisive_bonus += DECISIVE_HIT_VALUE
    

    decisive_bonus = min(decisive_bonus, W_DECISIVE)
    



    effective_w_kw = W_KW
    if decisive_hits:


        effective_w_kw = W_KW * 0.7
        logger.debug(f"Decisive evidence present ({len(decisive_hits)} hits), reducing keyword weight: {W_KW} → {effective_w_kw:.3f}")
    
    score = W_SIM * base_sim + effective_w_kw * keyword_score + decisive_bonus
    

    if coherence > 0.6:
        coherence_boost = (coherence - 0.6) * 0.1
        score += coherence_boost
    elif coherence < 0.3:
        coherence_penalty = (0.3 - coherence) * 0.1
        score -= coherence_penalty
    

    if not has_name_match and keyword_score < 0.1:

        score *= 0.5
    

    score = max(0.0, min(1.0, score))
    
    logger.debug(
        f"Hybrid score: sim={base_sim:.3f}, kw={keyword_score:.3f}, "
        f"decisive={decisive_bonus:.3f}, coherence={coherence:.3f}, "
        f"has_name={has_name_match} → {score:.3f}"
    )
    
    return score


def score_suspects(
    case_id: int,
    evidence_docs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Score all suspects for a case based on evidence with polarity-aware decisive evidence classification.
    
    This function uses an LLM-based polarity classifier to correctly handle decisive evidence.
    For example:
    - "CCTV shows John Doe entering" → positive (boosts score)
    - "No CCTV footage of John Doe" → negative (penalizes score)
    - "The CCTV system was installed by John Doe's company" → neutral (no effect)
    
    Args:
        case_id: Case ID
        evidence_docs: List of evidence documents from extract_evidence_context()
        
    Returns:
        List of scored suspects, sorted by score (descending), each containing:
            - suspect_id: Database ID
            - suspect_name: Suspect name
            - score: Final hybrid score [0, 1]
            - matched_clues: List of evidence clues (strings)
            - components: Scoring components (base_sim, keyword_score)
            - reasoning_trace: List of reasoning trace entries showing how score was calculated
            - contributing_docs: Top 3 contributing documents
            
    Example:
        >>> docs = extract_evidence_context(case_id=1)
        >>> ranked = score_suspects(case_id=1, docs)
        >>> for suspect in ranked:
        ...     print(f"{suspect['suspect_name']}: {suspect['score']:.2f}")
        ...     for line in suspect.get('reasoning_trace', []):
        ...         print(f"  {line}")
    """
    logger.info(f"🎯 Scoring suspects for case {case_id}")
    

    suspects = get_suspects_by_case(case_id)
    
    if not suspects:
        logger.warning(f"No suspects found for case {case_id}")
        return []
    

    if not evidence_docs:
        logger.warning("No evidence provided - returning zero scores")
        return [
            {
                'suspect_id': suspect.id,
                'suspect_name': suspect.name,
                'score': 0.0,
                'matched_clues': ['No evidence available'],
                'components': {'base_sim': 0.0, 'keyword_score': 0.0},
                'reasoning_trace': ['No evidence available for analysis'],
                'contributing_docs': []
            }
            for suspect in suspects
        ]
    

    evidence_texts = [doc['text'] for doc in evidence_docs]
    source_types = [doc.get('source_type', 'unknown') for doc in evidence_docs]


    evidence_scores = []
    for doc in evidence_docs:
        rag_score = doc.get('score', 1.0)


        relevance = max(0.0, 1.0 - (rag_score / 2.0)) if rag_score > 0 else 1.0
        evidence_scores.append(relevance)
    

    scored_suspects = []
    
    for suspect in suspects:
        logger.debug(f"Scoring suspect: {suspect.name}")
        

        reasoning_trace = []
        

        extra_terms = []
        metadata = suspect.metadata_json if suspect.metadata_json else {}
        if metadata:

            for key in ['vehicle', 'vehicles', 'known_vehicles', 'workplace', 'occupation']:
                if key in metadata:
                    value = metadata[key]
                    if isinstance(value, list):
                        extra_terms.extend([str(v) for v in value])
                    elif value:
                        extra_terms.append(str(value))
        

        kw_features = _keyword_features(evidence_texts, suspect.name, extra_terms, metadata)
        has_name_match = kw_features['name_hits'] > 0
        

        if kw_features['name_hits'] > 0:

            name_score_contribution = min(kw_features['name_hits'] * 0.02, 0.25) * W_KW
            reasoning_trace.append(f"+{name_score_contribution:.3f} name mentioned {kw_features['name_hits']} time(s)")
        
        if kw_features['term_hits'] > 0:

            term_score_contribution = min(kw_features['term_hits'] * 0.015, 0.3) * W_KW
            reasoning_trace.append(f"+{term_score_contribution:.3f} associated terms found ({kw_features['term_hits']} matches)")
        

















        decisive_hits_by_term = defaultdict(list)
        
        for doc in evidence_docs:
            text = doc.get('text', '')
            if not text:
                continue
            

            decisive_sentences = _find_decisive_sentences(text, suspect.name)
            
            for sentence, term in decisive_sentences:
                decisive_hits_by_term[term].append((sentence, doc.get('doc_id', 'unknown')))
        

        decisive_total = 0.0
        decisive_hits_for_hybrid = []
        
        for term, sentence_list in decisive_hits_by_term.items():

            term_weight = DECISIVE_WEIGHTS.get(term, DEFAULT_DECISIVE_WEIGHT)
            

            pos_count = 0
            neg_count = 0
            neu_count = 0
            positive_sentences = []
            negative_sentences = []
            
            for sentence, doc_id in sentence_list:

                polarity = classify_decisive_polarity(sentence, suspect.name, term)
                
                if polarity == "positive":
                    pos_count += 1
                    positive_sentences.append(sentence)
                    decisive_hits_for_hybrid.append(term)
                elif polarity == "negative":
                    neg_count += 1
                    negative_sentences.append(sentence)
                else:
                    neu_count += 1
            

            net_effect = (pos_count - neg_count) * term_weight
            decisive_total += net_effect
            

            if net_effect > 0:

                reasoning_trace.append(
                    f"+{net_effect:.3f} aggregated decisive weight for {term!r}: "
                    f"{pos_count} positive, {neg_count} negative, {neu_count} neutral"
                )
                logger.debug(
                    f"✅ Aggregated {term}: {pos_count} pos, {neg_count} neg, {neu_count} neu → "
                    f"net +{net_effect:.3f}"
                )
            elif net_effect < 0:

                reasoning_trace.append(
                    f"{net_effect:.3f} aggregated decisive weight for {term!r}: "
                    f"{pos_count} positive, {neg_count} negative, {neu_count} neutral"
                )
                logger.debug(
                    f"❌ Aggregated {term}: {pos_count} pos, {neg_count} neg, {neu_count} neu → "
                    f"net {net_effect:.3f}"
                )
            else:

                if pos_count > 0 or neg_count > 0:
                    reasoning_trace.append(
                        f"+0.000 aggregated decisive weight for {term!r}: "
                        f"{pos_count} positive, {neg_count} negative, {neu_count} neutral (balanced)"
                    )
                    logger.debug(
                        f"⚪ Aggregated {term}: {pos_count} pos, {neg_count} neg, {neu_count} neu → "
                        f"balanced (net 0.000)"
                    )

        



        if decisive_total > 0:
            decisive_bonus = min(decisive_total, W_DECISIVE)
        elif decisive_total < 0:

            decisive_bonus = max(decisive_total, -W_DECISIVE)
        else:
            decisive_bonus = 0.0
        


        kw_features['decisive_hits'] = decisive_hits_for_hybrid
        

        vs_features = _vector_similarity(
            suspect.profile_text, 
            evidence_texts,
            source_types=source_types,
            evidence_scores=evidence_scores
        )
        

        if vs_features['base_sim'] > 0:
            sim_contribution = vs_features['base_sim'] * W_SIM
            reasoning_trace.append(f"+{sim_contribution:.3f} semantic similarity with evidence corpus")
        



        hybrid_base = _hybrid_score(
            vs_features['base_sim'],
            kw_features['keyword_score'],
            decisive_hits_for_hybrid,
            coherence=vs_features.get('coherence', 0.0),
            has_name_match=has_name_match
        )
        


        old_decisive_bonus = 0.0
        for hit in decisive_hits_for_hybrid:
            if hit in RARE_TERMS:
                old_decisive_bonus += RARE_TERMS[hit]
            else:
                old_decisive_bonus += DECISIVE_HIT_VALUE
        old_decisive_bonus = min(old_decisive_bonus, W_DECISIVE)
        

        final_score = hybrid_base - old_decisive_bonus + decisive_bonus
        

        coherence = vs_features.get('coherence', 0.0)
        if coherence > 0.6:
            coherence_boost = (coherence - 0.6) * 0.1
            reasoning_trace.append(f"+{coherence_boost:.3f} evidence coherence boost")
        elif coherence < 0.3:
            coherence_penalty = (0.3 - coherence) * 0.1
            reasoning_trace.append(f"-{coherence_penalty:.3f} evidence coherence penalty (contradictory evidence)")
        


        vision_boost, vision_matches = _vision_ai_crosscheck(evidence_docs, suspect.name, metadata)
        if vision_boost > 0:
            if vision_matches:

                matches_str = ", ".join(vision_matches)
                reasoning_trace.append(f"+{vision_boost:.3f} vision cross-check: {matches_str}")
            else:
                reasoning_trace.append(f"+{vision_boost:.3f} vision AI cross-check match")
        final_score += vision_boost
        

        timeline_boost = 0.0
        try:
            timeline_events = build_timeline(case_id, suspect_id=suspect.id)
            murder_time = get_murder_time_from_evidence(case_id)
            timeline_score, timeline_trace = _timeline_score(suspect, timeline_events, murder_time)
            reasoning_trace.extend(timeline_trace)
            timeline_boost = timeline_score
            final_score += timeline_score
        except Exception as e:
            logger.warning(f"Error in timeline engine scoring: {e}")

            timeline_boost = _timeline_consistency(evidence_docs, metadata)
            if timeline_boost > 0:
                reasoning_trace.append(f"+{timeline_boost:.3f} timeline consistency with murder window")
            elif timeline_boost < 0:
                reasoning_trace.append(f"{timeline_boost:.3f} timeline inconsistency penalty")
            final_score += timeline_boost
        

        try:
            contradiction_graph = build_contradiction_graph(evidence_docs)
            if contradiction_graph is not None:
                contradictions = detect_contradictions(evidence_docs)
                add_contradiction_edges(contradiction_graph, contradictions)
                contradiction_penalty, contradiction_trace = _contradiction_penalty(contradiction_graph, suspect.name)
                reasoning_trace.append(contradiction_trace)
                final_score += contradiction_penalty
        except Exception as e:
            logger.warning(f"Error in contradiction graph: {e}")

        


        has_timeline_presence = False
        for doc in evidence_docs:
            text = doc.get('text', '').lower()
            source_type = doc.get('source_type', '').lower()

            if (source_type in ['cctv', 'witness', 'statement'] and 
                suspect.name.lower() in text):
                has_timeline_presence = True
                break
        

        zero_timeline_presence = False
        if not has_timeline_presence:
            zero_timeline_presence = True
            if metadata.get('alibi_confirmed', False) or metadata.get('alibi_verified', False):
                final_score -= 0.25
                reasoning_trace.append("-0.250 confirmed alibi contradicts evidence (no timeline presence)")
                logger.debug(f"Zero timeline presence + confirmed alibi penalty: -0.25")
            else:
                final_score -= 0.15
                reasoning_trace.append("-0.150 suspect absent in timeline evidence")
                logger.debug(f"Zero timeline presence penalty: -0.15")
        

        confirmed_alibi_far = False
        if (metadata.get('alibi_confirmed', False) or metadata.get('alibi_verified', False)):

            if 'financial' in str(metadata).lower() or 'dispute' in str(metadata).lower():


                if kw_features['keyword_score'] > 0.3:
                    reduction = (kw_features['keyword_score'] - 0.3) * 0.5
                    final_score -= reduction
                    confirmed_alibi_far = True
                    reasoning_trace.append(f"-{reduction:.3f} business dispute + confirmed alibi penalty")
                    logger.debug(f"Business dispute + confirmed alibi: reducing keyword boost by {reduction:.3f}")
        

        graph_boost = _cross_evidence_graph(
            evidence_docs,
            suspect.name,
            extra_terms,
            kw_features['decisive_hits']
        )
        if graph_boost > 0:
            reasoning_trace.append(f"+{graph_boost:.3f} cross-evidence graph match")
        final_score += graph_boost
        



        vehicle_penalty = _detect_vehicle_contradictions(evidence_texts, extra_terms, metadata)
        if vehicle_penalty > 0.05:
            reasoning_trace.append(f"-{vehicle_penalty:.3f} vehicle mismatch penalty")
        

        location_boost = _location_triangulation(evidence_texts, metadata)
        if location_boost > 0:
            reasoning_trace.append(f"+{location_boost:.3f} location triangulation match")
            final_score += location_boost
        

        MAX_SCORE = 1.0
        final_score = min(final_score, MAX_SCORE)
        final_score = max(0.0, final_score)
        

        if not reasoning_trace and final_score < 0.1:
            reasoning_trace.append("Weak evidence correlation - no significant matches found")
        

        def parse_impact(line):
            """Extract numeric impact from reasoning trace line"""
            match = re.search(r'([+-]?)(\d+\.?\d*)', line)
            if match:
                sign = -1 if match.group(1) == '-' else 1
                value = float(match.group(2))
                return sign * value
            return 0.0
        
        reasoning_trace.sort(key=lambda x: abs(parse_impact(x)), reverse=True)
        

        logger.info(
            f"Suspect {suspect.name}: vision_boost={vision_boost:.3f}, "
            f"graph_boost={graph_boost:.3f}, timeline_boost={timeline_boost:.3f}, "
            f"final_score={final_score:.3f}"
        )
        

        matched_clues = []
        
        if kw_features['name_hits'] > 0:
            matched_clues.append(f"Name mentioned {kw_features['name_hits']} time(s) in evidence")
        
        if kw_features['term_hits'] > 0:
            matched_clues.append(f"Associated terms found ({kw_features['term_hits']} matches)")
        
        if kw_features['decisive_hits']:
            matched_clues.append(f"Decisive evidence: {', '.join(kw_features['decisive_hits'])}")
        
        if vs_features['base_sim'] > 0.5:
            matched_clues.append(f"High profile similarity ({vs_features['base_sim']:.2f})")
        


        if vision_boost > 0:
            if vision_matches:

                for match_desc in vision_matches:
                    matched_clues.append(match_desc)
            else:

                matched_clues.append(f"Vision AI match (+{vision_boost:.2f})")
        
        if graph_boost > 0:
            matched_clues.append(f"Multiple evidence connections (+{graph_boost:.2f})")
        
        if timeline_boost > 0:
            matched_clues.append(f"Timeline consistency (+{timeline_boost:.2f})")
        
        if not matched_clues:
            matched_clues.append("Weak evidence correlation")
        


        doc_scores = []
        for i, doc in enumerate(evidence_docs):
            if i < len(vs_features['sims']):
                doc_scores.append({
                    'doc_id': doc['doc_id'],
                    'title': doc['title'],
                    'score': vs_features['sims'][i]
                })
        

        doc_scores.sort(key=lambda x: x['score'], reverse=True)
        contributing_docs = doc_scores[:3]
        

        scored_suspects.append({
            'suspect_id': suspect.id,
            'suspect_name': suspect.name,
            'score': final_score,
            'matched_clues': matched_clues,
            'components': {
                'base_sim': vs_features['base_sim'],
                'keyword_score': kw_features['keyword_score'],
                'decisive_bonus': min(len(kw_features['decisive_hits']) * DECISIVE_HIT_VALUE, W_DECISIVE)
            },
            'reasoning_trace': reasoning_trace,
            'contributing_docs': contributing_docs
        })
    

    scored_suspects.sort(key=lambda x: (-x['score'], x['suspect_name']))
    
    logger.info(f"✅ Scored {len(scored_suspects)} suspects")
    
    return scored_suspects


def correlate_and_persist(
    case_id: int,
    query: Optional[str] = None,
    k: int = 8
) -> Dict[str, Any]:
    """
    High-level entry point: extract evidence, score suspects, persist results
    
    Args:
        case_id: Case ID to analyze
        query: Optional search query (uses DEFAULT_QUERY if None)
        k: Number of evidence documents to retrieve
        
    Returns:
        Dictionary with:
            - case_id: Case ID
            - query: Query used
            - docs_used: Number of evidence documents used
            - ranked: List of scored suspects
            - persisted: Whether results were persisted to DB
            
        Or error dictionary if insufficient evidence:
            - error: 'insufficient_evidence'
            - case_id: Case ID
            - message: Error message
            
    Example:
        >>> result = correlate_and_persist(case_id=1, query="Who is most likely responsible?")
        >>> 
        >>> if 'error' not in result:
        ...     for suspect in result['ranked']:
        ...         print(f"{suspect['suspect_name']}: {suspect['score']:.2f}")
        ...         print(f"  Clues: {', '.join(suspect['matched_clues'])}")
    """
    logger.info(f"🔬 Correlating evidence for case {case_id}")
    

    case = get_case(case_id)
    if not case:
        return {
            'error': 'case_not_found',
            'case_id': case_id,
            'message': f"Case {case_id} not found in database"
        }
    

    evidence_docs = extract_evidence_context(case_id, query, k)
    

    ranked = score_suspects(case_id, evidence_docs)
    

    if len(evidence_docs) == 0 and len(ranked) == 0:
        logger.warning(f"Insufficient evidence for case {case_id} - not persisting")
        return {
            'error': 'insufficient_evidence',
            'case_id': case_id,
            'message': 'No evidence or suspects found for analysis',
            'docs_used': 0,
            'ranked': []
        }
    

    persisted = False
    if ranked and any(r['score'] > 0 for r in ranked):

        db_results = []
        for suspect_data in ranked:
            db_results.append({
                'suspect_id': suspect_data['suspect_id'],
                'score': suspect_data['score'],
                'matched_clues': {
                    'clues': suspect_data['matched_clues'],
                    'components': suspect_data['components'],
                    'contributing_docs': suspect_data['contributing_docs'],
                    'reasoning_trace': suspect_data.get('reasoning_trace', [])
                }
            })
        

        success = save_analysis_results(case_id, db_results)
        
        if success:
            persisted = True
            logger.info(f"✅ Persisted {len(db_results)} analysis results to database")
        else:
            logger.error("Failed to persist analysis results")
    

    return {
        'case_id': case_id,
        'query': query or DEFAULT_QUERY,
        'docs_used': len(evidence_docs),
        'ranked': ranked,
        'persisted': persisted
    }


def pretty_rankings(ranked: List[Dict[str, Any]]) -> str:
    """
    Format rankings as readable text (for Streamlit or CLI)
    
    Args:
        ranked: List of scored suspects from score_suspects()
        
    Returns:
        Formatted string with rankings
        
    Example:
        >>> ranked = score_suspects(case_id=1, evidence_docs=docs)
        >>> print(pretty_rankings(ranked))
        Suspect Rankings
        ================
        1. John Doe (0.85)
           - Name mentioned 3 time(s) in evidence
           - Decisive evidence: fingerprints, dna
        ...
    """
    if not ranked:
        return "No suspects to rank"
    
    lines = ["Suspect Rankings", "=" * 50, ""]
    
    for i, suspect in enumerate(ranked, 1):
        lines.append(f"{i}. {suspect['suspect_name']} ({suspect['score']:.2f})")
        
        for clue in suspect['matched_clues']:
            lines.append(f"   - {clue}")
        
        if suspect['contributing_docs']:
            lines.append(f"   Contributing evidence:")
            for doc in suspect['contributing_docs']:
                title = doc['title'] or doc['doc_id']
                lines.append(f"     • {title} (sim: {doc['score']:.2f})")
        
        lines.append("")
    
    return "\n".join(lines)



if __name__ == "__main__":
    """
    Quick test of evidence correlator
    Run with: python -m app.tools.evidence_correlator
    """
    print("=" * 60)
    print("Evidence Correlator Test")
    print("=" * 60)
    
    from app.db import get_all_cases
    
    cases = get_all_cases()
    
    if not cases:
        print("\n⚠️  No cases found in database")
        print("Run: python example_db_usage.py to create sample data")
        exit(0)
    

    case_with_data = None
    for case in cases:
        suspects = get_suspects_by_case(case.id)
        status = get_case_index_status(case.id)
        
        if suspects and status.get('indexed'):
            case_with_data = case
            break
    
    if not case_with_data:
        print("\n⚠️  No cases with suspects and indexed evidence found")
        print("Add suspects and evidence, then run: build_case_index(case_id)")
        exit(0)
    
    print(f"\n📁 Found case: {case_with_data.title}")
    

    print(f"\n🔬 Correlating evidence...")
    result = correlate_and_persist(case_with_data.id)
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        print(f"   {result.get('message', '')}")
    else:
        print(f"\n✅ Analysis complete!")
        print(f"   Documents used: {result['docs_used']}")
        print(f"   Suspects ranked: {len(result['ranked'])}")
        print(f"   Persisted to DB: {result['persisted']}")
        
        print(f"\n{pretty_rankings(result['ranked'])}")
    
    print("\n✅ Evidence correlator test complete!")

