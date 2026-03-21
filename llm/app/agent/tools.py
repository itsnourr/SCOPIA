"""
LangChain Tools for Forensic Agent

Custom tools that the agent can call to retrieve case information and analyze text.
"""

import logging
from typing import Optional

try:
    from langchain.tools import tool
except ImportError:

    from langchain_core.tools import tool

from app.db.dao import get_case, get_suspects_by_case, get_texts_by_case, get_images_by_case, get_analysis_results
from app.tools.timeline_extractor import extract_timeline_events
from app.rag.vectorstore import query_documents as _query_documents
from app.agent.utils import format_context
from collections import defaultdict


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


@tool("get_case_summary", return_direct=False)
def get_case_summary(case_id: int) -> str:
    """
    Returns a comprehensive summarized description of the current case,
    including suspects, evidence breakdown, key findings, timeline, and correlation results.
    
    Use this tool when the user asks about:
    - Case overview or summary
    - Summarize the case
    - Case information
    - General case details
    
    Args:
        case_id: The case ID to summarize
        
    Returns:
        A comprehensive formatted string with case summary including:
        - Case title and description
        - Suspects with brief profiles
        - Evidence breakdown by type
        - Key findings from evidence (using RAG)
        - Timeline overview
        - Latest correlation results
    """
    try:
        case = get_case(case_id)
        if not case:
            return f"Case {case_id} not found in database."
        
        suspects = get_suspects_by_case(case_id)
        texts = get_texts_by_case(case_id)
        images = get_images_by_case(case_id)
        

        summary_lines = []
        summary_lines.append(f"=== CASE SUMMARY ===\n")
        summary_lines.append(f"Case: {case.title}\n")
        summary_lines.append(f"Description: {case.description}\n")
        summary_lines.append(f"Created: {case.created_at.strftime('%Y-%m-%d')}\n\n")
        

        summary_lines.append(f"=== SUSPECTS ({len(suspects)}) ===\n")
        if suspects:
            for suspect in suspects:
                summary_lines.append(f"- {suspect.name}")
                if suspect.profile_text:

                    profile_preview = suspect.profile_text[:100] + "..." if len(suspect.profile_text) > 100 else suspect.profile_text
                    summary_lines.append(f"  Profile: {profile_preview}")
                if suspect.metadata_json:
                    metadata_str = ", ".join([f"{k}: {v}" for k, v in suspect.metadata_json.items() if v])
                    if metadata_str:
                        summary_lines.append(f"  Metadata: {metadata_str}")
                summary_lines.append("")
        else:
            summary_lines.append("No suspects added yet.\n")
        

        summary_lines.append(f"=== EVIDENCE BREAKDOWN ===\n")
        summary_lines.append(f"Text Documents: {len(texts)} total\n")
        

        texts_by_type = defaultdict(list)
        for text in texts:
            texts_by_type[text.source_type].append(text)
        
        type_labels = {
            "witness_statement": "Witness Statements",
            "forensic_report": "Forensic Reports",
            "cctv_video": "CCTV/Timeline Evidence",
            "timeline": "Timeline Evidence",
            "digital_evidence": "Digital Evidence",
            "scene_notes": "Scene Notes",
            "physical_object": "Physical Objects",
            "autopsy_report": "Autopsy Reports",
            "alibi": "Alibi Evidence",
            "other": "Other Evidence"
        }
        
        for source_type, type_texts in texts_by_type.items():
            label = type_labels.get(source_type, source_type.replace('_', ' ').title())
            summary_lines.append(f"  - {label}: {len(type_texts)} document(s)")
        summary_lines.append("")
        
        summary_lines.append(f"Images: {len(images)} total")
        analyzed_images = [img for img in images if img.caption_text]
        if analyzed_images:
            summary_lines.append(f"  - Analyzed: {len(analyzed_images)}")
        summary_lines.append("")
        

        try:
            key_docs = _query_documents(
                query="key evidence findings forensic analysis murder weapon fingerprints DNA timeline",
                case_id=case_id,
                k=min(10, len(texts) + len(analyzed_images)) if (texts or analyzed_images) else 0
            )
            
            if key_docs:
                summary_lines.append(f"=== KEY FINDINGS ===\n")

                for i, doc in enumerate(key_docs[:5], 1):

                    metadata = doc.get('metadata', {})
                    doc_title = metadata.get('title') or metadata.get('doc_id') or 'Unknown Document'
                    doc_type = metadata.get('source_type', 'unknown')

                    content = doc.get('text', doc.get('page_content', ''))
                    
                    summary_lines.append(f"{i}. [{doc_title}] ({doc_type})")
                    if content:
                        preview = content[:150] + "..." if len(content) > 150 else content
                        summary_lines.append(f"   {preview}")
                    summary_lines.append("")
        except Exception as e:
            logger.warning(f"Could not retrieve key findings: {e}")
        

        try:
            from app.db.models import TimelineEvent
            from app.db.session import SessionLocal
            with SessionLocal() as session:
                timeline_events = session.query(TimelineEvent).filter(
                    TimelineEvent.case_id == case_id
                ).order_by(TimelineEvent.timestamp).limit(10).all()
                
                if timeline_events:
                    summary_lines.append(f"=== TIMELINE OVERVIEW ===\n")
                    for event in timeline_events[:5]:
                        event_type = event.event_type
                        timestamp = event.timestamp.strftime('%Y-%m-%d %H:%M:%S') if event.timestamp else "Unknown"
                        suspect_info = f" ({event.suspect.name})" if event.suspect else ""
                        summary_lines.append(f"- {event_type}{suspect_info} at {timestamp}")
                    summary_lines.append("")
        except Exception as e:
            logger.warning(f"Could not retrieve timeline: {e}")
        

        try:
            analysis_results = get_analysis_results(case_id)
            if analysis_results:

                results_by_run = defaultdict(list)
                for result in analysis_results:
                    results_by_run[result.run_at].append(result)
                
                if results_by_run:
                    latest_run_time = max(results_by_run.keys())
                    latest_results = results_by_run[latest_run_time]
                    

                    latest_results_sorted = sorted(latest_results, key=lambda x: x.score_float, reverse=True)
                    
                    summary_lines.append(f"=== LATEST CORRELATION RESULTS ===\n")
                    summary_lines.append(f"Analysis Date: {latest_run_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
                    for i, result in enumerate(latest_results_sorted[:3], 1):
                        try:
                            suspect_name = result.suspect.name if result.suspect else "Unknown"
                        except Exception:
                            suspect_id = result.suspect_id
                            suspect = next((s for s in suspects if s.id == suspect_id), None)
                            suspect_name = suspect.name if suspect else "Unknown"
                        
                        summary_lines.append(f"{i}. {suspect_name}: Score {result.score_float:.3f}")
                    
                    summary_lines.append("")
        except Exception as e:
            logger.warning(f"Could not retrieve analysis results: {e}")
        
        summary = "\n".join(summary_lines)
        logger.info(f"✅ Generated comprehensive case summary for case {case_id}")
        return summary
        
    except Exception as e:
        logger.error(f"❌ Error generating case summary: {e}")
        return f"Error generating case summary: {str(e)}"


@tool("analyze_timeline_text", return_direct=False)
def analyze_timeline_text(text: str, case_id: Optional[int] = None) -> str:
    """
    Extracts timeline events (arrival, departure, sightings, timestamps)
    from arbitrary text provided by the user.
    
    Use this tool when the user provides text and asks you to:
    - Extract timeline information
    - Find events or timestamps
    - Analyze when things happened
    
    Args:
        text: The text content to analyze for timeline events
        case_id: Optional case ID for context (if available)
        
    Returns:
        A formatted string listing all extracted timeline events with:
        - Event type (arrival, departure, etc.)
        - Timestamp
        - Confidence score
        - Original text snippet
    """
    try:
        if not text or not text.strip():
            return "No text provided for timeline analysis."
        

        doc_id = f"user_input_{case_id}" if case_id else "user_input"
        case_id_for_extraction = case_id if case_id else 0
        

        events = extract_timeline_events(text, doc_id=doc_id, case_id=case_id_for_extraction)
        
        if not events:
            return "No timeline events were detected in the provided text."
        

        formatted_events = []
        for event in events:
            event_type = event.get('event_type', 'unknown')
            timestamp = event.get('timestamp', 'unknown')
            confidence = event.get('confidence', 0.0)
            raw_text = event.get('raw_text', '')
            suspect = event.get('suspect')
            
            event_str = f"- **{event_type}**"
            if suspect:
                event_str += f" by {suspect}"
            event_str += f" at {timestamp}"
            event_str += f" (confidence: {confidence:.2f})"
            if raw_text:
                event_str += f"\n  Text: \"{raw_text}\""
            
            formatted_events.append(event_str)
        
        result = f"Extracted {len(events)} timeline event(s):\n\n" + "\n\n".join(formatted_events)
        
        logger.info(f"✅ Extracted {len(events)} timeline events from text")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error analyzing timeline text: {e}")
        return f"Error analyzing timeline: {str(e)}"


@tool("vector_search", return_direct=False)
def vector_search(query: str, case_id: int, k: int = 10) -> str:
    """
    Performs semantic search over case evidence using RAG (Retrieval-Augmented Generation).
    This tool searches the vector database for documents relevant to the query.
    
    Use this tool when the user asks about:
    - Evidence in the case
    - Information about suspects, vehicles, locations, or events
    - Questions that require searching through case documents
    - Any query that needs evidence retrieval
    
    This is the PRIMARY tool for evidence retrieval. Always use this tool when
    the user asks questions about case evidence, suspects, or events.
    
    Args:
        query: The search query text (what to search for)
        case_id: The case ID to search within (required for case isolation)
        k: Number of top documents to retrieve (default: 10, max recommended: 30)
        
    Returns:
        A formatted string containing:
        - Number of documents found
        - Each document with:
          - Document ID and title
          - Source type (witness, report, image, etc.)
          - Relevance score
          - Document content excerpt
        - Documents are sorted by relevance (most relevant first)
        
    Example:
        >>> result = vector_search("red car near crime scene", case_id=1, k=5)
        >>> print(result)
        EVIDENCE CONTEXT (3 documents):
        
        1. [text_1: Witness Statement - John Doe] (witness_statement, relevance: 0.85)
           "Witness saw red sedan parked near the crime scene at 3pm..."
    """
    try:
        if not query or not query.strip():
            return "Error: Empty query provided to vector search."
        
        if not case_id:
            return "Error: case_id is required for vector search."
        

        docs = _query_documents(
            query=query,
            case_id=case_id,
            k=k
        )
        
        if not docs:
            return f"No relevant documents found for query: '{query}' in case {case_id}."
        

        formatted_result = format_context(docs, max_tokens=2000)
        
        logger.info(f"✅ Vector search completed: {len(docs)} documents retrieved for query '{query}'")
        return formatted_result
        
    except Exception as e:
        logger.error(f"❌ Error in vector search tool: {e}")
        return f"Error performing vector search: {str(e)}"

