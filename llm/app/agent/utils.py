"""
Utility functions for the forensic agent module
"""

from typing import List, Dict, Any


def format_context(docs: List[Dict[str, Any]], max_tokens: int = 2000) -> str:
    """
    Format retrieved documents into compact, cited context
    
    Args:
        docs: List of documents from RAG
        max_tokens: Approximate token limit for context
        
    Returns:
        Formatted context string
        
    Example:
        >>> docs = [{'doc_id': 'T1', 'title': 'Witness A', 'text': '...', 'score': 0.88}]
        >>> context = format_context(docs)
        >>> print(context)
        EVIDENCE CONTEXT (3 documents):
        
        1. [T1: Witness A] (witness, relevance: 0.88)
           "Witness saw suspect near scene at 3pm..."
    """
    if not docs:
        return "NO EVIDENCE AVAILABLE\n\nNo relevant documents found in the case database."
    
    lines = [f"EVIDENCE CONTEXT ({len(docs)} documents):\n"]
    
    char_count = 0
    char_limit = max_tokens * 4
    
    for i, doc in enumerate(docs, 1):

        metadata = doc.get('metadata', {})
        doc_id = doc.get('doc_id') or metadata.get('doc_id', 'unknown')
        title = doc.get('title') or metadata.get('title', 'Untitled')
        text = doc.get('text', '')
        source_type = doc.get('source_type') or metadata.get('source_type', 'unknown')
        score = doc.get('score', 0.0)
        

        header = f"\n{i}. [{doc_id}: {title}] ({source_type}, relevance: {score:.2f})"
        


        extract = text[:500].strip()
        if len(text) > 500:
            extract += "..."
        
        body = f'   "{extract}"'
        

        entry = header + "\n" + body + "\n"
        if char_count + len(entry) > char_limit and i > 2:
            lines.append(f"\n[{len(docs) - i + 1} additional documents truncated to stay within token limit]")
            break
        
        lines.append(entry)
        char_count += len(entry)
    
    return "\n".join(lines)

