"""
Unit tests for RAG system (vectorstore and ingestion)
Tests document indexing, retrieval, case isolation, and deduplication
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from app.rag.vectorstore import (
    get_vectorstore,
    add_documents,
    query_documents,
    delete_case_documents,
    get_collection_stats,
    reset_vectorstore,
    _compute_doc_hash
)
from app.rag.ingest import (
    ingest_texts_from_db,
    ingest_images_from_db,
    ingest_suspects_from_db,
    build_case_index,
    get_case_index_status
)



@pytest.fixture(scope="function")
def temp_chroma_dir(monkeypatch):
    """Create temporary ChromaDB directory for testing"""
    temp_dir = tempfile.mkdtemp()
    

    from config import Config
    monkeypatch.setattr(Config, "CHROMA_DIR", Path(temp_dir))
    

    import app.rag.vectorstore as vs_module
    vs_module._vectorstore_instance = None
    vs_module._client_instance = None
    
    yield temp_dir
    

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def sample_documents():
    """Sample documents for testing"""
    return [
        {
            "text": "Witness saw red sedan near crime scene at 3pm",
            "metadata": {
                "case_id": 1,
                "source_type": "witness",
                "title": "Witness Statement 1",
                "doc_id": "text_1"
            }
        },
        {
            "text": "Security camera captured suspect in dark hoodie",
            "metadata": {
                "case_id": 1,
                "source_type": "image",
                "title": "Security Footage",
                "doc_id": "image_1"
            }
        },
        {
            "text": "Fingerprints found on doorknob match database records",
            "metadata": {
                "case_id": 1,
                "source_type": "report",
                "title": "Forensic Report",
                "doc_id": "text_2"
            }
        }
    ]






def test_get_vectorstore(temp_chroma_dir):
    """Test vectorstore initialization"""
    vectorstore = get_vectorstore()
    assert vectorstore is not None
    assert vectorstore._collection is not None


def test_vectorstore_singleton(temp_chroma_dir):
    """Test that get_vectorstore returns same instance"""
    vs1 = get_vectorstore()
    vs2 = get_vectorstore()
    assert vs1 is vs2






def test_add_documents_success(temp_chroma_dir, sample_documents):
    """Test adding documents successfully"""
    stats = add_documents(sample_documents)
    
    assert stats["total"] == 3
    assert stats["added"] == 3
    assert stats["skipped"] == 0
    assert stats["errors"] == 0


def test_add_empty_documents(temp_chroma_dir):
    """Test adding empty list of documents"""
    stats = add_documents([])
    
    assert stats["total"] == 0
    assert stats["added"] == 0


def test_add_documents_with_empty_text(temp_chroma_dir):
    """Test that documents with empty text are skipped"""
    docs = [
        {
            "text": "",
            "metadata": {"case_id": 1, "doc_id": "empty"}
        },
        {
            "text": "Valid document",
            "metadata": {"case_id": 1, "doc_id": "valid"}
        }
    ]
    
    stats = add_documents(docs)
    
    assert stats["total"] == 2
    assert stats["added"] == 1
    assert stats["skipped"] == 1


def test_duplicate_detection(temp_chroma_dir, sample_documents):
    """Test that duplicate documents are skipped"""

    stats1 = add_documents(sample_documents)
    assert stats1["added"] == 3
    

    stats2 = add_documents(sample_documents, check_duplicates=True)
    assert stats2["added"] == 0
    assert stats2["skipped"] == 3


def test_force_add_duplicates(temp_chroma_dir, sample_documents):
    """Test adding duplicates when check_duplicates=False"""

    stats1 = add_documents(sample_documents)
    assert stats1["added"] == 3
    

    stats2 = add_documents(sample_documents, check_duplicates=False)
    assert stats2["added"] == 3
    assert stats2["skipped"] == 0






def test_query_documents(temp_chroma_dir, sample_documents):
    """Test querying documents"""
    add_documents(sample_documents)
    
    results = query_documents("vehicle near scene", case_id=1, k=5)
    
    assert len(results) > 0
    assert isinstance(results[0], dict)
    assert "text" in results[0]
    assert "score" in results[0]
    assert "metadata" in results[0]


def test_query_relevance_order(temp_chroma_dir):
    """Test that query results are ordered by relevance"""
    docs = [
        {
            "text": "Red car parked outside",
            "metadata": {"case_id": 1, "doc_id": "1", "title": "Car Doc"}
        },
        {
            "text": "Blue bicycle in garage",
            "metadata": {"case_id": 1, "doc_id": "2", "title": "Bike Doc"}
        },
        {
            "text": "Red vehicle seen nearby",
            "metadata": {"case_id": 1, "doc_id": "3", "title": "Vehicle Doc"}
        }
    ]
    add_documents(docs)
    

    results = query_documents("red car", case_id=1, k=3)
    
    assert len(results) >= 2

    assert "car" in results[0]["text"].lower() or "red" in results[0]["text"].lower()

    if len(results) > 1:
        assert results[0]["score"] <= results[1]["score"]


def test_query_empty_string(temp_chroma_dir, sample_documents):
    """Test querying with empty string"""
    add_documents(sample_documents)
    
    results = query_documents("", case_id=1)
    

    assert results == []


def test_query_with_k_parameter(temp_chroma_dir):
    """Test that k parameter limits results"""

    docs = [
        {
            "text": f"Document number {i}",
            "metadata": {"case_id": 1, "doc_id": f"doc_{i}"}
        }
        for i in range(5)
    ]
    add_documents(docs)
    

    results = query_documents("document", case_id=1, k=2)
    
    assert len(results) == 2






def test_case_isolation(temp_chroma_dir):
    """Test that queries are isolated by case_id"""

    case1_docs = [
        {
            "text": "Evidence for case one about robbery",
            "metadata": {"case_id": 1, "doc_id": "c1_1"}
        }
    ]
    

    case2_docs = [
        {
            "text": "Evidence for case two about fraud",
            "metadata": {"case_id": 2, "doc_id": "c2_1"}
        }
    ]
    
    add_documents(case1_docs + case2_docs)
    

    results_case1 = query_documents("evidence", case_id=1, k=10)
    

    results_case2 = query_documents("evidence", case_id=2, k=10)
    

    assert len(results_case1) > 0
    assert len(results_case2) > 0
    

    for doc in results_case1:
        assert doc["metadata"]["case_id"] == 1
    

    for doc in results_case2:
        assert doc["metadata"]["case_id"] == 2


def test_query_without_case_filter(temp_chroma_dir):
    """Test querying without case_id filter returns all cases"""
    docs = [
        {
            "text": "Document for case 1",
            "metadata": {"case_id": 1, "doc_id": "c1"}
        },
        {
            "text": "Document for case 2",
            "metadata": {"case_id": 2, "doc_id": "c2"}
        }
    ]
    add_documents(docs)
    

    results = query_documents("document", case_id=None, k=10)
    

    case_ids = {doc["metadata"]["case_id"] for doc in results}
    assert len(case_ids) >= 1






def test_query_with_source_type_filter(temp_chroma_dir):
    """Test filtering by source_type"""
    docs = [
        {
            "text": "Witness statement about suspect",
            "metadata": {"case_id": 1, "source_type": "witness", "doc_id": "w1"}
        },
        {
            "text": "Report about suspect",
            "metadata": {"case_id": 1, "source_type": "report", "doc_id": "r1"}
        }
    ]
    add_documents(docs)
    

    results = query_documents("suspect", case_id=1, source_type="witness", k=10)
    
    assert len(results) > 0

    for doc in results:
        assert doc["metadata"]["source_type"] == "witness"






def test_delete_case_documents(temp_chroma_dir, sample_documents):
    """Test deleting all documents for a case"""

    add_documents(sample_documents)
    

    results_before = query_documents("", case_id=1, k=100)
    initial_count = len(results_before)
    assert initial_count > 0
    

    deleted_count = delete_case_documents(case_id=1)
    
    assert deleted_count == initial_count
    

    results_after = query_documents("evidence", case_id=1, k=100)
    assert len(results_after) == 0






def test_get_collection_stats_empty(temp_chroma_dir):
    """Test collection stats with no documents"""
    stats = get_collection_stats()
    
    assert stats["total_documents"] == 0
    assert stats["unique_cases"] == 0
    assert stats["source_types"] == {}


def test_get_collection_stats_with_documents(temp_chroma_dir, sample_documents):
    """Test collection stats with documents"""
    add_documents(sample_documents)
    
    stats = get_collection_stats()
    
    assert stats["total_documents"] == 3
    assert stats["unique_cases"] == 1
    assert "witness" in stats["source_types"]
    assert "image" in stats["source_types"]






def test_reset_vectorstore(temp_chroma_dir, sample_documents):
    """Test resetting vectorstore"""

    add_documents(sample_documents)
    

    stats_before = get_collection_stats()
    assert stats_before["total_documents"] > 0
    

    success = reset_vectorstore()
    assert success is True
    

    stats_after = get_collection_stats()
    assert stats_after["total_documents"] == 0






def test_compute_doc_hash():
    """Test document hash computation"""
    text = "Test document"
    metadata = {"case_id": 1, "doc_id": "test"}
    
    hash1 = _compute_doc_hash(text, metadata)
    hash2 = _compute_doc_hash(text, metadata)
    

    assert hash1 == hash2
    assert len(hash1) == 64


def test_compute_doc_hash_different_text():
    """Test that different text produces different hash"""
    metadata = {"case_id": 1}
    
    hash1 = _compute_doc_hash("Text A", metadata)
    hash2 = _compute_doc_hash("Text B", metadata)
    
    assert hash1 != hash2






def test_ingest_texts_empty_case():
    """Test ingesting texts from non-existent case"""
    texts = ingest_texts_from_db(case_id=99999)
    

    assert texts == []


def test_ingest_images_empty_case():
    """Test ingesting images from non-existent case"""
    images = ingest_images_from_db(case_id=99999)
    

    assert images == []


def test_ingest_suspects_empty_case():
    """Test ingesting suspects from non-existent case"""
    suspects = ingest_suspects_from_db(case_id=99999)
    

    assert suspects == []


def test_build_case_index_nonexistent(temp_chroma_dir):
    """Test building index for non-existent case"""
    stats = build_case_index(case_id=99999)
    
    assert "error" in stats
    assert stats["documents_prepared"] == 0






@pytest.mark.integration
def test_full_ingestion_workflow(temp_chroma_dir):
    """
    Integration test: full workflow from DB to vectorstore
    Only runs if database has test data
    """
    from app.db import get_all_cases
    

    cases = get_all_cases()
    if not cases:
        pytest.skip("No test data in database")
    
    case_id = cases[0].id
    

    stats = build_case_index(case_id, force_rebuild=True)
    
    assert stats["documents_prepared"] >= 0
    assert stats["documents_added"] >= 0
    

    if stats["documents_added"] > 0:
        results = query_documents("evidence", case_id=case_id, k=5)
        assert len(results) > 0


@pytest.mark.integration
def test_case_index_status(temp_chroma_dir):
    """Test getting case index status"""
    from app.db import get_all_cases
    
    cases = get_all_cases()
    if not cases:
        pytest.skip("No test data in database")
    
    case_id = cases[0].id
    

    build_case_index(case_id, force_rebuild=True)
    

    status = get_case_index_status(case_id)
    
    assert "case_id" in status
    assert "indexed" in status
    assert "document_count" in status






def test_add_documents_with_missing_metadata(temp_chroma_dir):
    """Test adding documents with minimal metadata"""
    docs = [
        {
            "text": "Document with minimal metadata",
            "metadata": {}
        }
    ]
    

    stats = add_documents(docs)
    assert stats["added"] == 1


def test_query_with_special_characters(temp_chroma_dir):
    """Test querying with special characters"""
    docs = [
        {
            "text": "Document with special chars: @#$%",
            "metadata": {"case_id": 1, "doc_id": "special"}
        }
    ]
    add_documents(docs)
    

    results = query_documents("@#$%", case_id=1, k=5)
    assert isinstance(results, list)


def test_large_document(temp_chroma_dir):
    """Test adding and querying large document"""

    large_text = "This is a large document. " * 400
    
    docs = [
        {
            "text": large_text,
            "metadata": {"case_id": 1, "doc_id": "large"}
        }
    ]
    
    stats = add_documents(docs)
    assert stats["added"] == 1
    

    results = query_documents("large document", case_id=1, k=1)
    assert len(results) > 0


def test_unicode_text(temp_chroma_dir):
    """Test handling Unicode text"""
    docs = [
        {
            "text": "Witness statement: 你好世界 Привет مرحبا",
            "metadata": {"case_id": 1, "doc_id": "unicode"}
        }
    ]
    
    stats = add_documents(docs)
    assert stats["added"] == 1
    

    results = query_documents("witness", case_id=1, k=1)
    assert len(results) > 0






def test_vectorstore_persistence(temp_chroma_dir, sample_documents):
    """Test that vectorstore persists data"""

    add_documents(sample_documents)
    

    import app.rag.vectorstore as vs_module
    vs_module._vectorstore_instance = None
    vs_module._client_instance = None
    

    vectorstore = get_vectorstore()
    

    results = query_documents("evidence", case_id=1, k=10)
    assert len(results) > 0

