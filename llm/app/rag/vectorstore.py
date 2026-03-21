"""
Vector Store Management for Forensic Crime Analysis Agent
Uses ChromaDB for persistent vector storage and semantic search

This module provides:
- Persistent ChromaDB vector store
- Document ingestion with deduplication
- Semantic search with case isolation
- Metadata filtering

Example Usage:
    >>> from app.rag.vectorstore import get_vectorstore, add_documents, query_documents
    >>> 
    >>> # Add documents
    >>> docs = [
    ...     {
    ...         "text": "Witness saw red car near the house at 3pm",
    ...         "metadata": {"case_id": 1, "source_type": "witness", "title": "Statement 1"}
    ...     }
    ... ]
    >>> add_documents(docs)
    >>> 
    >>> # Query documents
    >>> results = query_documents("red vehicle", case_id=1, k=5)
    >>> for doc in results:
    ...     print(doc["text"], doc["score"])
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

from config import Config


logger = logging.getLogger(__name__)


_vectorstore_instance: Optional[Chroma] = None
_client_instance: Optional[chromadb.Client] = None


def _get_embeddings():
    """
    Get embeddings model (singleton pattern)
    Uses HuggingFace sentence-transformers
    
    Returns:
        Embeddings model instance
    """


    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    logger.info("✅ Loaded embeddings model: all-MiniLM-L6-v2")
    return embeddings


def _ensure_chroma_dir():
    """Ensure ChromaDB directory exists"""
    chroma_dir = Path(Config.CHROMA_DIR)
    chroma_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"ChromaDB directory: {chroma_dir}")


def get_chroma_client() -> chromadb.Client:
    """
    Get or create ChromaDB client (persistent)
    
    Returns:
        ChromaDB client instance
    """
    global _client_instance
    
    if _client_instance is None:
        _ensure_chroma_dir()
        

        _client_instance = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(Config.CHROMA_DIR),
                anonymized_telemetry=False
            )
        )
        logger.info(f"✅ ChromaDB client initialized (persistent mode)")
    
    return _client_instance


def get_vectorstore() -> Chroma:
    """
    Get or create singleton Chroma vectorstore instance
    
    Returns:
        Chroma vectorstore with persistent storage
        
    Example:
        >>> vectorstore = get_vectorstore()
        >>> vectorstore.similarity_search("red car", k=5)
    """
    global _vectorstore_instance
    
    if _vectorstore_instance is None:
        _ensure_chroma_dir()
        

        embeddings = _get_embeddings()
        

        _vectorstore_instance = Chroma(
            collection_name=Config.CHROMA_COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(Config.CHROMA_DIR)
        )
        
        logger.info(
            f"✅ Vectorstore initialized: {Config.CHROMA_COLLECTION_NAME} "
            f"at {Config.CHROMA_DIR}"
        )
    
    return _vectorstore_instance


def _compute_doc_hash(text: str, metadata: Dict[str, Any]) -> str:
    """
    Compute unique hash for document to avoid duplicates
    
    Args:
        text: Document text
        metadata: Document metadata (case_id, doc_id, etc.)
        
    Returns:
        SHA-256 hash as hex string
    """

    unique_str = f"{text}|{metadata.get('case_id')}|{metadata.get('doc_id')}"
    return hashlib.sha256(unique_str.encode()).hexdigest()


def add_documents(docs: List[Dict[str, Any]], check_duplicates: bool = True) -> Dict[str, Any]:
    """
    Add documents to vectorstore with deduplication
    
    Args:
        docs: List of document dictionaries, each containing:
            - text: Document content (required)
            - metadata: Dictionary with case_id, source_type, title, doc_id, etc.
        check_duplicates: If True, skip documents that already exist
        
    Returns:
        Dictionary with ingestion statistics:
            - total: Total documents provided
            - added: Documents successfully added
            - skipped: Documents skipped (duplicates)
            - errors: Number of errors
            
    Example:
        >>> docs = [
        ...     {
        ...         "text": "Witness statement...",
        ...         "metadata": {
        ...             "case_id": 1,
        ...             "source_type": "witness",
        ...             "title": "Statement 1",
        ...             "doc_id": "text_1"
        ...         }
        ...     }
        ... ]
        >>> stats = add_documents(docs)
        >>> print(f"Added {stats['added']} documents")
    """
    if not docs:
        logger.warning("No documents provided for ingestion")
        return {"total": 0, "added": 0, "skipped": 0, "errors": 0}
    
    vectorstore = get_vectorstore()
    
    stats = {
        "total": len(docs),
        "added": 0,
        "skipped": 0,
        "errors": 0
    }
    

    existing_hashes = set()
    if check_duplicates:
        try:

            collection = vectorstore._collection
            all_docs = collection.get()
            if all_docs and all_docs.get('metadatas'):
                existing_hashes = {
                    meta.get('doc_hash') 
                    for meta in all_docs['metadatas'] 
                    if meta.get('doc_hash')
                }
            logger.debug(f"Found {len(existing_hashes)} existing document hashes")
        except Exception as e:
            logger.warning(f"Could not check existing documents: {e}")
    

    documents_to_add = []
    
    for doc in docs:
        try:
            text = doc.get("text", "").strip()
            metadata = doc.get("metadata", {})
            
            if not text:
                logger.warning("Skipping empty document")
                stats["skipped"] += 1
                continue
            

            doc_hash = _compute_doc_hash(text, metadata)
            

            if check_duplicates and doc_hash in existing_hashes:
                logger.debug(f"Skipping duplicate document: {metadata.get('title', 'Untitled')}")
                stats["skipped"] += 1
                continue
            

            metadata["doc_hash"] = doc_hash
            

            if "case_id" not in metadata:
                logger.warning("Document missing case_id in metadata")
            

            langchain_doc = Document(
                page_content=text,
                metadata=metadata
            )
            
            documents_to_add.append(langchain_doc)
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            stats["errors"] += 1
    

    if documents_to_add:
        try:
            vectorstore.add_documents(documents_to_add)
            stats["added"] = len(documents_to_add)
            
            logger.info(
                f"✅ Added {stats['added']} documents to vectorstore "
                f"(skipped {stats['skipped']} duplicates)"
            )
        except Exception as e:
            logger.error(f"Error adding documents to vectorstore: {e}")
            stats["errors"] += len(documents_to_add)
    
    return stats


def query_documents(
    query: str,
    case_id: Optional[int] = None,
    k: Optional[int] = None,
    source_type: Optional[str] = None,
    score_threshold: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Query vectorstore for relevant documents with optional filtering
    
    Args:
        query: Search query text
        case_id: Filter by case ID (recommended for case isolation)
        k: Maximum number of results to return (None = no limit, use threshold instead)
        source_type: Optional filter by source type (witness, report, image, etc.)
        score_threshold: Maximum relevance score (lower = more relevant). 
                        If provided, returns all documents with score <= threshold.
                        If None and k is None, uses default threshold of 1.5.
        
    Returns:
        List of document dictionaries with:
            - text: Document content
            - score: Relevance score (lower is more relevant)
            - metadata: Document metadata
            
    Example:
        >>> # Search with threshold (all relevant docs)
        >>> results = query_documents("red car", case_id=1, score_threshold=1.2)
        >>> 
        >>> # Search with fixed count
        >>> results = query_documents("red car", case_id=1, k=5)
    """
    if not query or not query.strip():
        logger.warning("Empty query provided")
        return []
    
    vectorstore = get_vectorstore()
    

    filter_dict = {}
    conditions = []
    
    if case_id is not None:
        conditions.append({"case_id": case_id})
    if source_type:
        conditions.append({"source_type": source_type})
    

    if len(conditions) > 1:
        filter_dict = {"$and": conditions}
    elif len(conditions) == 1:
        filter_dict = conditions[0]
    




    if score_threshold is not None:

        max_k = k if k is not None else 50
        use_threshold = True
    elif k is None:

        score_threshold = 1.5
        max_k = 50
        use_threshold = True
    else:

        max_k = k
        use_threshold = False
    
    try:

        if filter_dict:
            results = vectorstore.similarity_search_with_score(
                query,
                k=max_k,
                filter=filter_dict
            )
            logger.debug(f"Query: '{query}' with filter: {filter_dict} -> {len(results)} results")
        else:
            results = vectorstore.similarity_search_with_score(query, k=max_k)
            logger.debug(f"Query: '{query}' (no filter) -> {len(results)} results")
        

        formatted_results = []
        for doc, score in results:

            if use_threshold and score > score_threshold:
                continue
            
            formatted_results.append({
                "text": doc.page_content,
                "score": float(score),
                "metadata": doc.metadata
            })
        
        logger.info(f"✅ Retrieved {len(formatted_results)} relevant documents (threshold={score_threshold if use_threshold else 'N/A'}, max_k={max_k})")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error querying vectorstore: {e}")
        return []


def delete_case_documents(case_id: int) -> int:
    """
    Delete all documents for a specific case
    
    Args:
        case_id: Case ID to delete documents for
        
    Returns:
        Number of documents deleted
    """
    try:
        vectorstore = get_vectorstore()
        collection = vectorstore._collection
        

        results = collection.get(
            where={"case_id": case_id}
        )
        
        if results and results.get('ids'):
            doc_ids = results['ids']
            collection.delete(ids=doc_ids)
            
            logger.info(f"✅ Deleted {len(doc_ids)} documents for case {case_id}")
            return len(doc_ids)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error deleting case documents: {e}")
        return 0


def get_collection_stats() -> Dict[str, Any]:
    """
    Get statistics about the vectorstore collection
    
    Returns:
        Dictionary with:
            - total_documents: Total number of documents
            - unique_cases: Number of unique cases
            - source_types: Count by source type
    """
    try:
        vectorstore = get_vectorstore()
        collection = vectorstore._collection
        

        results = collection.get()
        
        if not results or not results.get('metadatas'):
            return {
                "total_documents": 0,
                "unique_cases": 0,
                "source_types": {}
            }
        
        metadatas = results['metadatas']
        

        unique_cases = set(meta.get('case_id') for meta in metadatas if meta.get('case_id'))
        

        source_types = {}
        for meta in metadatas:
            source = meta.get('source_type', 'unknown')
            source_types[source] = source_types.get(source, 0) + 1
        
        stats = {
            "total_documents": len(metadatas),
            "unique_cases": len(unique_cases),
            "source_types": source_types
        }
        
        logger.info(f"📊 Collection stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {
            "total_documents": 0,
            "unique_cases": 0,
            "source_types": {}
        }


def reset_vectorstore() -> bool:
    """
    Reset vectorstore by deleting all documents
    ⚠️ WARNING: This deletes all data!
    
    Returns:
        True if successful, False otherwise
    """
    try:
        vectorstore = get_vectorstore()
        collection = vectorstore._collection
        

        results = collection.get()
        if results and results.get('ids'):
            collection.delete(ids=results['ids'])
            logger.warning(f"⚠️  Deleted {len(results['ids'])} documents from vectorstore")
        
        return True
        
    except Exception as e:
        logger.error(f"Error resetting vectorstore: {e}")
        return False



if __name__ == "__main__":
    """
    Quick test of vectorstore functionality
    Run with: python -m app.rag.vectorstore
    """
    print("=" * 60)
    print("ChromaDB Vectorstore Test")
    print("=" * 60)
    

    print("\n📦 Initializing vectorstore...")
    vectorstore = get_vectorstore()
    print("✅ Vectorstore ready")
    

    print("\n📝 Adding sample documents...")
    sample_docs = [
        {
            "text": "Witness saw a red sedan parked near the crime scene at 3pm on Tuesday",
            "metadata": {
                "case_id": 1,
                "source_type": "witness",
                "title": "Witness Statement - John Doe",
                "doc_id": "text_1"
            }
        },
        {
            "text": "Security camera captured suspect wearing dark hoodie entering through back door",
            "metadata": {
                "case_id": 1,
                "source_type": "image",
                "title": "Security Footage - Rear Entrance",
                "doc_id": "image_1"
            }
        },
        {
            "text": "Fingerprints found on doorknob match database records",
            "metadata": {
                "case_id": 1,
                "source_type": "report",
                "title": "Forensic Analysis Report",
                "doc_id": "text_2"
            }
        },
        {
            "text": "Victim reported suspicious person loitering near house the previous evening",
            "metadata": {
                "case_id": 1,
                "source_type": "witness",
                "title": "Victim Statement",
                "doc_id": "text_3"
            }
        }
    ]
    
    stats = add_documents(sample_docs)
    print(f"✅ Added {stats['added']} documents (skipped {stats['skipped']} duplicates)")
    

    print("\n🔍 Testing semantic search...")
    queries = [
        "vehicle near crime scene",
        "suspicious clothing",
        "evidence analysis"
    ]
    
    for query in queries:
        print(f"\n📌 Query: '{query}'")
        results = query_documents(query, case_id=1, k=2)
        
        for i, doc in enumerate(results, 1):
            print(f"  {i}. [{doc['score']:.3f}] {doc['metadata']['title']}")
            print(f"     {doc['text'][:60]}...")
    

    print("\n🔒 Testing case isolation...")
    print("Adding document for case 2...")
    add_documents([{
        "text": "Different case entirely - bank robbery on Main Street",
        "metadata": {
            "case_id": 2,
            "source_type": "report",
            "title": "Case 2 Report",
            "doc_id": "text_99"
        }
    }])
    
    print("\nQuerying case 1 only:")
    results_case1 = query_documents("bank", case_id=1, k=5)
    print(f"  Found {len(results_case1)} results for case 1")
    
    print("\nQuerying case 2 only:")
    results_case2 = query_documents("bank", case_id=2, k=5)
    print(f"  Found {len(results_case2)} results for case 2")
    

    print("\n📊 Collection statistics:")
    stats = get_collection_stats()
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Unique cases: {stats['unique_cases']}")
    print(f"  By source type: {stats['source_types']}")
    
    print("\n✅ Vectorstore test complete!")

