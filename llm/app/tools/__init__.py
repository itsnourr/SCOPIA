"""
Custom LangChain tools for forensic analysis

Available Tools:
- Image Analyzer: Extract EXIF and generate captions for evidence images
- Evidence Correlator: Score suspects against evidence using hybrid scoring

Example Usage:
    >>> from app.tools import analyze_image, correlate_and_persist
    >>> 
    >>> # Analyze an evidence image
    >>> result = analyze_image(image_id=1)
    >>> print(result['caption'])
    >>> 
    >>> # Rebuild RAG index
    >>> from app.rag import build_case_index
    >>> build_case_index(case_id=1)
    >>> 
    >>> # Correlate evidence with suspects
    >>> result = correlate_and_persist(case_id=1)
    >>> for suspect in result['ranked']:
    ...     print(f"{suspect['suspect_name']}: {suspect['score']:.2f}")
"""

from app.tools.image_analyzer import (
    analyze_image,
    batch_analyze_images,
    extract_exif,
    generate_caption,
    DecryptionError,
    EXIFExtractionError,
    ImageAnalysisError
)

from app.tools.evidence_correlator import (
    correlate_and_persist,
    score_suspects,
    extract_evidence_context,
    pretty_rankings
)

from app.tools.llm_filter import (
    is_relevant_llm,
    get_llm_filter_status,
    reset_llm_filter_status
)

__all__ = [

    "analyze_image",
    "batch_analyze_images",
    "extract_exif",
    "generate_caption",
    

    "correlate_and_persist",
    "score_suspects",
    "extract_evidence_context",
    "pretty_rankings",
    

    "is_relevant_llm",
    "get_llm_filter_status",
    "reset_llm_filter_status",
    

    "ImageAnalysisError",
    "DecryptionError",
    "EXIFExtractionError",
]
