"""
Contradiction Graph

Builds a graph representation of evidence and detects contradictions between documents
using LLM-based analysis. Contradictions are used to penalize suspect scores.

Example Usage:
    >>> from app.tools.contradiction_graph import build_contradiction_graph, detect_contradictions
    >>> 
    >>> # Build graph from evidence documents
    >>> graph = build_contradiction_graph(evidence_docs)
    >>> 
    >>> # Detect contradictions
    >>> contradictions = detect_contradictions(evidence_docs)
    >>> 
    >>> # Add contradiction edges to graph
    >>> for doc1_id, doc2_id in contradictions:
    ...     graph.add_edge(doc1_id, doc2_id, type="contradiction")
"""

import logging
from typing import List, Dict, Any, Set, Tuple, Optional

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logging.warning("networkx not installed. Contradiction graph features will be limited.")

from app.llm_factory import create_llm

from config import Config


logger = logging.getLogger(__name__)


def build_contradiction_graph(evidence_docs: List[Dict[str, Any]]) -> Optional[Any]:
    """
    Build a graph representation of evidence documents.
    
    Args:
        evidence_docs: List of evidence document dictionaries with 'text' and metadata
        
    Returns:
        NetworkX Graph object, or None if networkx is not available
    """
    if not HAS_NETWORKX:
        logger.warning("networkx not available. Cannot build contradiction graph.")
        return None
    
    G = nx.Graph()
    
    for doc in evidence_docs:
        doc_id = doc.get("doc_id") or doc.get("metadata", {}).get("doc_id", f"doc_{len(G.nodes())}")
        G.add_node(doc_id, text=doc.get("text", ""), metadata=doc.get("metadata", {}))
    
    logger.debug(f"Built contradiction graph with {len(G.nodes())} nodes")
    return G


def detect_contradiction(doc_a_text: str, doc_b_text: str) -> bool:
    """
    Use LLM to detect if two documents contradict each other.
    
    Args:
        doc_a_text: Text content of first document
        doc_b_text: Text content of second document
        
    Returns:
        True if documents contradict, False otherwise
    """
    if not Config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not configured for contradiction detection. Returning False.")
        return False
    
    if not doc_a_text or not doc_b_text:
        return False
    

    prompt = f"""Compare the two evidence statements.
Determine if they contradict each other regarding suspects, time, location, or actions.

ETHICAL USE & RESPONSIBILITY:
- This system is for legitimate law enforcement and forensic investigation purposes only
- Analyze contradictions objectively based on factual statements
- Do not infer contradictions that are not explicitly present
- Maintain professional standards and ethical conduct at all times
- All analysis is decision support only, not a legal conclusion

Return EXACTLY one word: "contradiction", "consistent", or "unrelated".

--- Document A ---
{doc_a_text[:1000]}  # Limit length to avoid token limits

--- Document B ---
{doc_b_text[:1000]}  # Limit length to avoid token limits

Answer:"""

    try:
        llm = create_llm(temperature=0.0)
        
        response = llm.invoke(prompt)
        answer = response.content.strip().lower()
        

        if "contradiction" in answer:
            logger.debug("Contradiction detected between documents")
            return True
        else:
            return False
            
    except Exception as e:
        logger.warning(f"Error during contradiction detection: {e}")
        return False


def detect_contradictions(evidence_docs: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
    """
    Detect contradictions between all pairs of evidence documents.
    
    Args:
        evidence_docs: List of evidence document dictionaries
        
    Returns:
        List of tuples (doc_id_a, doc_id_b) for each detected contradiction
    """
    contradictions = []
    
    for i, doc_a in enumerate(evidence_docs):
        doc_a_id = doc_a.get("doc_id") or doc_a.get("metadata", {}).get("doc_id", f"doc_{i}")
        doc_a_text = doc_a.get("text", "")
        
        if not doc_a_text:
            continue
        
        for j, doc_b in enumerate(evidence_docs):
            if i >= j:
                continue
            
            doc_b_id = doc_b.get("doc_id") or doc_b.get("metadata", {}).get("doc_id", f"doc_{j}")
            doc_b_text = doc_b.get("text", "")
            
            if not doc_b_text:
                continue
            

            if detect_contradiction(doc_a_text, doc_b_text):
                contradictions.append((doc_a_id, doc_b_id))
                logger.debug(f"Contradiction detected: {doc_a_id} <-> {doc_b_id}")
    
    logger.info(f"Detected {len(contradictions)} contradictions among {len(evidence_docs)} documents")
    return contradictions


def add_contradiction_edges(graph: Any, contradictions: List[Tuple[str, str]]) -> None:
    """
    Add contradiction edges to the graph.
    
    Args:
        graph: NetworkX Graph object
        contradictions: List of (doc_id_a, doc_id_b) tuples
    """
    if not HAS_NETWORKX or graph is None:
        return
    
    for doc_id_a, doc_id_b in contradictions:
        if graph.has_node(doc_id_a) and graph.has_node(doc_id_b):
            graph.add_edge(doc_id_a, doc_id_b, type="contradiction")
            logger.debug(f"Added contradiction edge: {doc_id_a} <-> {doc_id_b}")


def _contradiction_penalty(graph: Any, suspect_name: Optional[str] = None) -> Tuple[float, str]:
    """
    Calculate penalty score based on contradictions in the graph.
    
    Args:
        graph: NetworkX Graph object with contradiction edges
        suspect_name: Optional suspect name for filtering (not used in current implementation)
        
    Returns:
        Tuple of (penalty_score, reasoning_message)
    """
    if not HAS_NETWORKX or graph is None:
        return 0.0, "+0.000 no contradiction graph available"
    
    contradiction_count = 0
    
    for edge in graph.edges(data=True):
        doc1, doc2, data = edge
        if data.get("type") == "contradiction":
            contradiction_count += 1
    
    if contradiction_count == 0:
        return 0.0, "+0.000 no contradictions detected"
    

    penalty = max(-0.25, -0.05 * contradiction_count)
    
    reasoning = f"{penalty:+.3f} contradiction penalty ({contradiction_count} contradiction(s))"
    
    return penalty, reasoning

