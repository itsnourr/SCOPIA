"""
Data Ingestion for RAG System
Loads documents from PostgreSQL database and indexes them in ChromaDB

This module handles:
- Loading text documents from database
- Loading image captions from database
- Building case-specific indices
- Tracking ingestion statistics

Example Usage:
    >>> from app.rag.ingest import build_case_index, ingest_texts_from_db
    >>> 
    >>> # Ingest all evidence for a case
    >>> build_case_index(case_id=1)
    >>> 
    >>> # Or ingest selectively
    >>> texts = ingest_texts_from_db(case_id=1)
    >>> images = ingest_images_from_db(case_id=1)
"""

import logging
import time
from typing import List, Dict, Any

from app.db import (
    get_texts_by_case,
    get_images_by_case,
    get_suspects_by_case,
    get_case
)
from app.rag.vectorstore import add_documents, get_collection_stats
from app.tools.llm_filter import is_relevant_llm, get_llm_filter_status, reset_llm_filter_status


logger = logging.getLogger(__name__)


def ingest_texts_from_db(case_id: int) -> List[Dict[str, Any]]:
    """
    Load all text documents for a case and prepare them for vectorization
    
    Args:
        case_id: Case ID to load documents for
        
    Returns:
        List of document dictionaries ready for vectorization:
            - text: Document content
            - metadata: Dictionary with case_id, source_type, title, doc_id
            
    Example:
        >>> texts = ingest_texts_from_db(case_id=1)
        >>> print(f"Loaded {len(texts)} text documents")
    """
    try:

        text_docs = get_texts_by_case(case_id)
        
        if not text_docs:
            logger.info(f"No text documents found for case {case_id}")
            return []
        

        prepared_docs = []
        filtered_count = 0
        
        for text_doc in text_docs:
            source_type = text_doc.source_type
            


            if source_type != "forensic":
                logger.info(f"🔍 Checking LLM relevance for text document: {text_doc.title} (type: {source_type})")
                if not is_relevant_llm(text_doc.content):
                    logger.info(f"❌ LLM filtered out irrelevant text evidence: {text_doc.title}")
                    filtered_count += 1
                    continue
                logger.info(f"✅ LLM kept relevant text evidence: {text_doc.title}")
            
            doc_dict = {
                "text": text_doc.content,
                "metadata": {
                    "case_id": text_doc.case_id,
                    "source_type": source_type,
                    "title": text_doc.title,
                    "doc_id": f"text_{text_doc.id}",
                    "db_id": text_doc.id,
                    "db_table": "text_documents"
                }
            }
            prepared_docs.append(doc_dict)
        
        logger.info(
            f"📄 Prepared {len(prepared_docs)} text documents for case {case_id} "
            f"({filtered_count} irrelevant documents filtered out)"
        )
        return prepared_docs
        
    except Exception as e:
        logger.error(f"Error ingesting texts from database: {e}")
        return []


def ingest_images_from_db(case_id: int) -> List[Dict[str, Any]]:
    """
    Load images with non-null caption_text for a case
    
    Args:
        case_id: Case ID to load images for
        
    Returns:
        List of document dictionaries with image captions:
            - text: Image caption text
            - metadata: Dictionary with case_id, source_type, title, doc_id, filename
            
    Example:
        >>> images = ingest_images_from_db(case_id=1)
        >>> print(f"Loaded {len(images)} image captions")
    """
    try:

        images = get_images_by_case(case_id)
        
        if not images:
            logger.info(f"No images found for case {case_id}")
            return []
        

        prepared_docs = []
        filtered_count = 0
        
        for image in images:

            if not image.caption_text or not image.caption_text.strip():
                continue
            

            logger.info(f"🔍 Checking LLM relevance for image: {image.filename}")
            if not is_relevant_llm(image.caption_text):
                logger.info(f"❌ LLM filtered out irrelevant image caption: {image.filename}")
                filtered_count += 1
                continue
            logger.info(f"✅ LLM kept relevant image: {image.filename}")
            

            title = f"Image: {image.filename}"
            if image.exif_json and image.exif_json.get('timestamp'):
                title += f" ({image.exif_json['timestamp']})"
            
            doc_dict = {
                "text": image.caption_text,
                "metadata": {
                    "case_id": image.case_id,
                    "source_type": "image",
                    "title": title,
                    "doc_id": f"image_{image.id}",
                    "db_id": image.id,
                    "db_table": "images",
                    "filename": image.filename,
                    "has_exif": bool(image.exif_json)
                }
            }
            prepared_docs.append(doc_dict)
        
        logger.info(
            f"🖼️  Prepared {len(prepared_docs)} image captions for case {case_id} "
            f"(from {len(images)} total images, {filtered_count} irrelevant images filtered out)"
        )
        return prepared_docs
        
    except Exception as e:
        logger.error(f"Error ingesting images from database: {e}")
        return []


def ingest_suspects_from_db(case_id: int) -> List[Dict[str, Any]]:
    """
    Load suspect profiles for a case
    
    Args:
        case_id: Case ID to load suspects for
        
    Returns:
        List of document dictionaries with suspect profiles:
            - text: Suspect profile text
            - metadata: Dictionary with case_id, source_type, title, suspect_id
    """
    try:

        suspects = get_suspects_by_case(case_id)
        
        if not suspects:
            logger.info(f"No suspects found for case {case_id}")
            return []
        

        prepared_docs = []
        
        for suspect in suspects:

            text_parts = [f"Suspect: {suspect.name}", suspect.profile_text]
            

            if suspect.metadata_json:
                if suspect.metadata_json.get('alibi'):
                    text_parts.append(f"Alibi: {suspect.metadata_json['alibi']}")
                if suspect.metadata_json.get('occupation'):
                    text_parts.append(f"Occupation: {suspect.metadata_json['occupation']}")
            
            doc_dict = {
                "text": "\n".join(text_parts),
                "metadata": {
                    "case_id": suspect.case_id,
                    "source_type": "suspect",
                    "title": f"Suspect Profile: {suspect.name}",
                    "doc_id": f"suspect_{suspect.id}",
                    "db_id": suspect.id,
                    "db_table": "suspects",
                    "suspect_id": suspect.id,
                    "suspect_name": suspect.name
                }
            }
            prepared_docs.append(doc_dict)
        
        logger.info(f"👤 Prepared {len(prepared_docs)} suspect profiles for case {case_id}")
        return prepared_docs
        
    except Exception as e:
        logger.error(f"Error ingesting suspects from database: {e}")
        return []


def build_case_index(
    case_id: int,
    include_texts: bool = True,
    include_images: bool = True,
    include_suspects: bool = True,
    force_rebuild: bool = False
) -> Dict[str, Any]:
    """
    Build complete vectorstore index for a case
    Combines texts, image captions, and suspect profiles
    
    Args:
        case_id: Case ID to build index for
        include_texts: Include text documents
        include_images: Include image captions
        include_suspects: Include suspect profiles
        force_rebuild: If True, delete existing documents first
        
    Returns:
        Dictionary with ingestion statistics:
            - case_id: Case ID processed
            - documents_prepared: Total documents prepared
            - documents_added: Documents successfully added
            - documents_skipped: Documents skipped (duplicates)
            - sources: Breakdown by source type
            - duration_seconds: Time taken
            - total_chars: Total characters indexed
            
    Example:
        >>> # Build complete index for case
        >>> stats = build_case_index(case_id=1)
        >>> print(f"Indexed {stats['documents_added']} documents in {stats['duration_seconds']:.1f}s")
        >>> 
        >>> # Rebuild index (delete existing first)
        >>> stats = build_case_index(case_id=1, force_rebuild=True)
    """
    logger.info(f"🚀 Starting case index build for case_id={case_id}")
    start_time = time.time()
    

    case = get_case(case_id)
    if not case:
        logger.error(f"Case {case_id} not found in database")
        return {
            "case_id": case_id,
            "error": "Case not found",
            "documents_prepared": 0,
            "documents_added": 0
        }
    
    logger.info(f"📁 Building index for: {case.title}")
    

    if force_rebuild:
        from app.rag.vectorstore import delete_case_documents
        deleted_count = delete_case_documents(case_id)
        logger.info(f"🗑️  Deleted {deleted_count} existing documents for case {case_id}")
    

    reset_llm_filter_status()
    

    all_docs = []
    sources_breakdown = {
        "texts": 0,
        "images": 0,
        "suspects": 0
    }
    

    if include_texts:
        text_docs = ingest_texts_from_db(case_id)
        all_docs.extend(text_docs)
        sources_breakdown["texts"] = len(text_docs)
        

        try:
            from app.tools.timeline_extractor import extract_timeline_events
            from app.db.dao import add_timeline_event
            from app.db import get_suspects_by_case
            

            suspects = get_suspects_by_case(case_id)
            suspect_name_to_id = {s.name.lower(): s.id for s in suspects}
            

            for text_doc in text_docs:
                doc_id = text_doc.get("metadata", {}).get("doc_id", "")
                text_content = text_doc.get("text", "")
                
                if not text_content or not doc_id:
                    continue
                

                events = extract_timeline_events(
                    text=text_content,
                    doc_id=doc_id,
                    case_id=case_id
                )
                

                for event in events:

                    suspect_id = None
                    if event.get("suspect"):
                        suspect_name_lower = event["suspect"].lower()
                        suspect_id = suspect_name_to_id.get(suspect_name_lower)
                    
                    event_dict = {
                        "case_id": case_id,
                        "suspect_id": suspect_id,
                        "source_doc_id": doc_id,
                        "raw_text": event.get("raw_text", ""),
                        "event_type": event.get("event_type", ""),
                        "timestamp": event.get("timestamp"),
                        "confidence": event.get("confidence", 1.0)
                    }
                    
                    add_timeline_event(event_dict)
                
                if events:
                    logger.debug(f"✅ Extracted {len(events)} timeline events from {doc_id}")
        except Exception as e:

            logger.warning(f"⚠️ Timeline extraction failed during indexing: {e}")
    

    if include_images:
        image_docs = ingest_images_from_db(case_id)
        all_docs.extend(image_docs)
        sources_breakdown["images"] = len(image_docs)
    

    if include_suspects:
        suspect_docs = ingest_suspects_from_db(case_id)
        all_docs.extend(suspect_docs)
        sources_breakdown["suspects"] = len(suspect_docs)
    

    filter_status = get_llm_filter_status()
    if filter_status['failed']:
        logger.warning(
            f"⚠️ LLM filtering failed during ingestion ({filter_status['failure_count']} failure(s)). "
            f"Some irrelevant documents may have been indexed."
        )
    

    total_chars = sum(len(doc["text"]) for doc in all_docs)
    
    logger.info(
        f"📊 Prepared {len(all_docs)} documents: "
        f"{sources_breakdown['texts']} texts, "
        f"{sources_breakdown['images']} images, "
        f"{sources_breakdown['suspects']} suspects"
    )
    

    if all_docs:
        ingest_stats = add_documents(all_docs, check_duplicates=not force_rebuild)
    else:
        logger.warning(f"No documents found to index for case {case_id}")
        ingest_stats = {"total": 0, "added": 0, "skipped": 0, "errors": 0}
    

    duration = time.time() - start_time
    

    result = {
        "case_id": case_id,
        "case_title": case.title,
        "documents_prepared": len(all_docs),
        "documents_added": ingest_stats["added"],
        "documents_skipped": ingest_stats["skipped"],
        "documents_errors": ingest_stats["errors"],
        "sources": sources_breakdown,
        "duration_seconds": round(duration, 2),
        "total_chars": total_chars,
        "avg_chars_per_doc": round(total_chars / len(all_docs)) if all_docs else 0,
        "llm_filter_failed": filter_status['failed'],
        "llm_filter_failure_count": filter_status['failure_count']
    }
    
    logger.info(
        f"✅ Case index build complete: "
        f"Added {result['documents_added']} documents "
        f"({result['total_chars']} chars) in {result['duration_seconds']}s"
    )
    
    return result


def rebuild_all_cases() -> Dict[str, Any]:
    """
    Rebuild indices for all cases in database
    ⚠️ This can take a long time for large databases
    
    Returns:
        Dictionary with overall statistics
    """
    from app.db import get_all_cases
    
    logger.info("🔄 Starting full database reindex...")
    start_time = time.time()
    
    cases = get_all_cases()
    
    if not cases:
        logger.warning("No cases found in database")
        return {"total_cases": 0, "total_documents": 0}
    
    total_stats = {
        "total_cases": len(cases),
        "total_documents_added": 0,
        "total_documents_skipped": 0,
        "case_results": []
    }
    
    for case in cases:
        logger.info(f"Processing case {case.id}: {case.title}")
        
        result = build_case_index(case.id, force_rebuild=True)
        
        total_stats["total_documents_added"] += result.get("documents_added", 0)
        total_stats["total_documents_skipped"] += result.get("documents_skipped", 0)
        total_stats["case_results"].append({
            "case_id": case.id,
            "title": case.title,
            "documents_added": result.get("documents_added", 0)
        })
    
    total_stats["duration_seconds"] = round(time.time() - start_time, 2)
    
    logger.info(
        f"✅ Full reindex complete: "
        f"{total_stats['total_cases']} cases, "
        f"{total_stats['total_documents_added']} documents indexed "
        f"in {total_stats['duration_seconds']}s"
    )
    
    return total_stats


def get_case_index_status(case_id: int) -> Dict[str, Any]:
    """
    Get indexing status for a specific case
    
    Args:
        case_id: Case ID to check
        
    Returns:
        Dictionary with:
            - case_id: Case ID
            - indexed: Whether case has any indexed documents
            - document_count: Number of indexed documents
            - source_breakdown: Count by source type
    """
    from app.rag.vectorstore import get_vectorstore
    
    try:

        vectorstore = get_vectorstore()
        


        try:
            collection = vectorstore._collection
        except AttributeError:

            try:
                from app.rag.vectorstore import get_chroma_client
                from config import Config
                client = get_chroma_client()
                collection = client.get_collection(Config.CHROMA_COLLECTION_NAME)
            except Exception:

                logger.debug(f"Collection doesn't exist yet")
                return {
                    "case_id": case_id,
                    "indexed": False,
                    "document_count": 0,
                    "source_breakdown": {}
                }
        



        results = None
        for case_id_value in [case_id, str(case_id)]:
            try:
                results = collection.get(
                    where={"case_id": case_id_value},
                    limit=10000
                )
                if results and results.get('ids'):
                    break
            except Exception:
                continue
        
        if not results or not results.get('ids'):

            logger.debug(f"Direct where clause failed, trying alternative")
            try:
                all_results = collection.get(limit=10000)
                
                if not all_results or not all_results.get('ids'):
                    return {
                        "case_id": case_id,
                        "indexed": False,
                        "document_count": 0,
                        "source_breakdown": {}
                    }
                

                filtered_ids = []
                filtered_metadatas = []
                for i, metadata in enumerate(all_results.get('metadatas', [])):
                    if metadata:

                        doc_case_id = metadata.get('case_id')
                        if doc_case_id is not None:

                            if isinstance(doc_case_id, str):
                                doc_case_id = int(doc_case_id)
                            if doc_case_id == case_id:
                                filtered_ids.append(all_results['ids'][i])
                                filtered_metadatas.append(metadata)
                
                if not filtered_ids:
                    return {
                        "case_id": case_id,
                        "indexed": False,
                        "document_count": 0,
                        "source_breakdown": {}
                    }
                
                results = {
                    'ids': filtered_ids,
                    'metadatas': filtered_metadatas
                }
            except Exception as e:
                logger.debug(f"Failed to get all documents: {e}")
                return {
                    "case_id": case_id,
                    "indexed": False,
                    "document_count": 0,
                    "source_breakdown": {}
                }
        
        if not results or not results.get('ids'):
            return {
                "case_id": case_id,
                "indexed": False,
                "document_count": 0,
                "source_breakdown": {}
            }
        

        source_breakdown = {}
        metadata_list = results.get('metadatas', [])
        
        for metadata in metadata_list:
            if metadata:
                source = metadata.get("source_type", "unknown")
                source_breakdown[source] = source_breakdown.get(source, 0) + 1
        
        document_count = len(results['ids'])
        
        logger.debug(f"Case {case_id} has {document_count} indexed documents")
        
        return {
            "case_id": case_id,
            "indexed": True,
            "document_count": document_count,
            "source_breakdown": source_breakdown
        }
        
    except Exception as e:
        logger.error(f"Error checking case index status: {e}", exc_info=True)
        return {
            "case_id": case_id,
            "indexed": False,
            "document_count": 0,
            "error": str(e)
        }



if __name__ == "__main__":
    """
    Quick test of ingestion functionality
    Run with: python -m app.rag.ingest
    """
    print("=" * 60)
    print("RAG Data Ingestion Test")
    print("=" * 60)
    

    from app.db import get_all_cases
    
    cases = get_all_cases()
    
    if not cases:
        print("\n⚠️  No cases found in database")
        print("Run: python example_db_usage.py to create sample data")
        exit(0)
    
    print(f"\n📊 Found {len(cases)} cases in database")
    

    case = cases[0]
    case_id = case.id
    
    print(f"\n📁 Testing ingestion for case: {case.title} (ID: {case_id})")
    

    print("\n1️⃣ Loading text documents...")
    texts = ingest_texts_from_db(case_id)
    print(f"   ✅ Loaded {len(texts)} text documents")
    if texts:
        print(f"      Example: {texts[0]['metadata']['title']}")
    
    print("\n2️⃣ Loading image captions...")
    images = ingest_images_from_db(case_id)
    print(f"   ✅ Loaded {len(images)} image captions")
    if images:
        print(f"      Example: {images[0]['metadata']['title']}")
    
    print("\n3️⃣ Loading suspect profiles...")
    suspects = ingest_suspects_from_db(case_id)
    print(f"   ✅ Loaded {len(suspects)} suspect profiles")
    if suspects:
        print(f"      Example: {suspects[0]['metadata']['title']}")
    

    print(f"\n4️⃣ Building complete index for case {case_id}...")
    stats = build_case_index(case_id, force_rebuild=True)
    
    print("\n📊 Indexing Statistics:")
    print(f"   Documents prepared: {stats['documents_prepared']}")
    print(f"   Documents added: {stats['documents_added']}")
    print(f"   Documents skipped: {stats['documents_skipped']}")
    print(f"   Total characters: {stats['total_chars']:,}")
    print(f"   Duration: {stats['duration_seconds']}s")
    print(f"\n   By source:")
    for source, count in stats['sources'].items():
        print(f"      {source}: {count}")
    

    print(f"\n5️⃣ Checking index status...")
    status = get_case_index_status(case_id)
    print(f"   Indexed: {status['indexed']}")
    print(f"   Documents: {status['document_count']}")
    print(f"   Sources: {status['source_breakdown']}")
    

    print("\n6️⃣ Collection statistics:")
    collection_stats = get_collection_stats()
    print(f"   Total documents: {collection_stats['total_documents']}")
    print(f"   Unique cases: {collection_stats['unique_cases']}")
    print(f"   By source: {collection_stats['source_types']}")
    
    print("\n✅ Ingestion test complete!")

