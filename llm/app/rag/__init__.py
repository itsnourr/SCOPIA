"""
RAG (Retrieval-Augmented Generation) module with ChromaDB

This module provides semantic search over forensic case evidence using:
- ChromaDB for vector storage
- HuggingFace embeddings (sentence-transformers)
- Document ingestion from PostgreSQL database
- Case-isolated retrieval

Example Usage:
    >>> from app.rag import build_case_index, query_documents
    >>> 
    >>> # Index all evidence for a case
    >>> build_case_index(case_id=1)
    >>> 
    >>> # Search for relevant evidence
    >>> results = query_documents("red car near house", case_id=1, k=5)
    >>> for doc in results:
    ...     print(f"{doc['score']:.3f} - {doc['metadata']['title']}")
"""


from app.rag.vectorstore import (
    get_vectorstore,
    get_chroma_client,
    add_documents,
    query_documents,
    delete_case_documents,
    get_collection_stats,
    reset_vectorstore
)


from app.rag.ingest import (
    ingest_texts_from_db,
    ingest_images_from_db,
    ingest_suspects_from_db,
    build_case_index,
    rebuild_all_cases,
    get_case_index_status
)

__all__ = [

    "get_vectorstore",
    "get_chroma_client",
    "add_documents",
    "query_documents",
    "delete_case_documents",
    "get_collection_stats",
    "reset_vectorstore",
    

    "ingest_texts_from_db",
    "ingest_images_from_db",
    "ingest_suspects_from_db",
    "build_case_index",
    "rebuild_all_cases",
    "get_case_index_status",
]
