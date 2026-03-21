# RAG (Retrieval-Augmented Generation) Module

Semantic search and document retrieval for forensic case evidence using ChromaDB and HuggingFace embeddings.

---

## 🎯 Overview

The RAG module enables:
- **Semantic search** over case documents (texts, witness statements, image captions)
- **Case isolation** - queries are filtered by case_id
- **Deduplication** - avoids re-indexing identical documents
- **Persistent storage** - ChromaDB data persists between runs
- **Multi-source indexing** - combines texts, images, and suspect profiles

---

## 📦 Components

### `vectorstore.py`
ChromaDB vector store management

**Key Functions:**
- `get_vectorstore()` - Get singleton Chroma instance
- `add_documents(docs)` - Add documents with deduplication
- `query_documents(query, case_id, k)` - Semantic search
- `delete_case_documents(case_id)` - Delete case data
- `get_collection_stats()` - Get statistics

### `ingest.py`
Data ingestion from PostgreSQL database

**Key Functions:**
- `ingest_texts_from_db(case_id)` - Load text documents
- `ingest_images_from_db(case_id)` - Load image captions
- `ingest_suspects_from_db(case_id)` - Load suspect profiles
- `build_case_index(case_id)` - Build complete index
- `get_case_index_status(case_id)` - Check indexing status

---

## 🚀 Quick Start

### 1. Index a Case

```python
from app.rag import build_case_index

# Index all evidence for case 1
stats = build_case_index(case_id=1)

print(f"Indexed {stats['documents_added']} documents")
print(f"Sources: {stats['sources']}")
print(f"Duration: {stats['duration_seconds']}s")
```

### 2. Search Evidence

```python
from app.rag import query_documents

# Search for relevant evidence
results = query_documents(
    query="red car near house",
    case_id=1,
    k=5
)

for doc in results:
    print(f"{doc['score']:.3f} - {doc['metadata']['title']}")
    print(f"  {doc['text'][:100]}...")
```

### 3. Case-Specific Search

```python
# Search only witness statements
results = query_documents(
    query="suspicious person",
    case_id=1,
    source_type="witness",
    k=3
)
```

---

## 📋 Complete Workflow

### From Database to Semantic Search

```python
from app.db import add_case, add_text, add_suspect
from app.rag import build_case_index, query_documents

# 1. Create case in database
case = add_case("Robbery Investigation", "Armed robbery...")

# 2. Add evidence
add_text(
    case_id=case.id,
    source_type="witness",
    title="Witness Statement",
    content="I saw a red sedan near the bank at 3pm..."
)

add_suspect(
    case_id=case.id,
    name="John Doe",
    profile_text="Known burglar with history of similar crimes..."
)

# 3. Build RAG index
stats = build_case_index(case.id)

# 4. Query evidence
results = query_documents("vehicle at bank", case_id=case.id, k=5)

for doc in results:
    print(f"Score: {doc['score']:.3f}")
    print(f"Type: {doc['metadata']['source_type']}")
    print(f"Title: {doc['metadata']['title']}")
    print(f"Text: {doc['text'][:200]}...\n")
```

---

## 🔍 Document Structure

### Input Format

```python
docs = [
    {
        "text": "Document content here",
        "metadata": {
            "case_id": 1,              # Required for case isolation
            "source_type": "witness",  # witness, report, image, suspect
            "title": "Document title",
            "doc_id": "text_123",      # Unique identifier
            "suspect_id": 5            # Optional: link to suspect
        }
    }
]
```

### Output Format

```python
results = query_documents("query", case_id=1, k=5)

# Returns list of:
[
    {
        "text": "Matched document content",
        "score": 0.234,  # Lower = more relevant
        "metadata": {
            "case_id": 1,
            "source_type": "witness",
            "title": "Witness Statement",
            ...
        }
    }
]
```

---

## 🗃️ Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | int | ✅ | Case ID for isolation |
| `source_type` | str | ✅ | witness, report, image, suspect |
| `title` | str | ✅ | Document title |
| `doc_id` | str | ✅ | Unique document identifier |
| `db_id` | int | ❌ | Database record ID |
| `db_table` | str | ❌ | Source database table |
| `suspect_id` | int | ❌ | Related suspect ID |
| `filename` | str | ❌ | Image filename |
| `doc_hash` | str | Auto | Hash for deduplication |

---

## 🧪 Testing

```bash
# Run all RAG tests
pytest app/tests/test_rag.py -v

# Run specific test
pytest app/tests/test_rag.py::test_query_documents -v

# Run with coverage
pytest app/tests/test_rag.py --cov=app.rag

# Test vectorstore directly
python -m app.rag.vectorstore

# Test ingestion directly
python -m app.rag.ingest
```

---

## 📊 Advanced Features

### Rebuild Index

```python
from app.rag import build_case_index

# Force rebuild (delete existing first)
stats = build_case_index(case_id=1, force_rebuild=True)
```

### Selective Ingestion

```python
# Index only texts (skip images and suspects)
stats = build_case_index(
    case_id=1,
    include_texts=True,
    include_images=False,
    include_suspects=False
)
```

### Delete Case Data

```python
from app.rag import delete_case_documents

# Remove all indexed documents for a case
deleted_count = delete_case_documents(case_id=1)
```

### Collection Statistics

```python
from app.rag import get_collection_stats

stats = get_collection_stats()
print(f"Total documents: {stats['total_documents']}")
print(f"Unique cases: {stats['unique_cases']}")
print(f"By source: {stats['source_types']}")
```

### Rebuild All Cases

```python
from app.rag import rebuild_all_cases

# Reindex entire database (can be slow)
stats = rebuild_all_cases()
print(f"Indexed {stats['total_documents_added']} documents")
print(f"Across {stats['total_cases']} cases")
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# ChromaDB storage directory
CHROMA_DIR=./data/chroma

# Collection name
CHROMA_COLLECTION_NAME=forensic_evidence
```

### Embedding Model

The module uses `sentence-transformers/all-MiniLM-L6-v2`:
- **Dimensions**: 384
- **Speed**: Fast inference on CPU
- **Quality**: Good balance for semantic search
- **Size**: ~80MB download on first use

To change the model, edit `vectorstore.py`:

```python
embeddings = HuggingFaceEmbeddings(
    model_name="your-model-name",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)
```

---

## 🔒 Case Isolation

**Critical**: Always filter by `case_id` to prevent cross-case evidence leakage:

```python
# ✅ GOOD: Case-specific search
results = query_documents("evidence", case_id=1, k=5)

# ⚠️ BAD: Global search (may return evidence from other cases)
results = query_documents("evidence", case_id=None, k=5)
```

---

## 🎯 Performance Tips

1. **Batch Indexing**: Use `build_case_index()` instead of adding documents one-by-one
2. **Deduplication**: Enable `check_duplicates=True` to avoid re-indexing
3. **K Parameter**: Set `k` to reasonable value (5-10) for faster queries
4. **Persistence**: Data persists automatically - no need to re-index on restart
5. **Case Filtering**: Always use `case_id` filter for faster, more relevant results

---

## 🐛 Troubleshooting

### "No module named 'sentence_transformers'"

```bash
pip install sentence-transformers
```

### "ChromaDB directory not found"

The directory is created automatically. Check `CHROMA_DIR` in `.env`:

```bash
CHROMA_DIR=./data/chroma
```

### "No documents found for case"

1. Check case has evidence in database:
   ```python
   from app.db import get_case_data
   data = get_case_data(case_id)
   print(data)
   ```

2. Rebuild index:
   ```python
   build_case_index(case_id, force_rebuild=True)
   ```

### "Query returns no results"

1. Verify documents are indexed:
   ```python
   from app.rag import get_case_index_status
   status = get_case_index_status(case_id)
   print(status)
   ```

2. Try broader query or increase `k`:
   ```python
   results = query_documents("crime", case_id=1, k=20)
   ```

### "Embeddings model download slow"

First-time download of sentence-transformers model (~80MB). Subsequent runs use cached model.

---

## 📈 Integration with Agent

The RAG module will be used by the LangChain agent for:

1. **Context Retrieval**: Get relevant evidence before answering questions
2. **Evidence Correlation**: Find similar evidence across documents
3. **Suspect Analysis**: Retrieve suspect profiles for comparison
4. **Question Answering**: Provide context for forensic questions

Example agent workflow:

```python
# User asks: "What vehicle was seen near the crime scene?"

# 1. Agent queries RAG
results = query_documents("vehicle crime scene", case_id=1, k=3)

# 2. Agent uses results as context
context = "\n".join([doc['text'] for doc in results])

# 3. Agent generates answer with context
answer = agent.run(query="What vehicle?", context=context)
```

---

## 🔄 Next Steps

After RAG is working:
1. **Build custom LangChain tools** (Image Analyzer, Evidence Correlator)
2. **Create LangChain agent** with Gemini Pro
3. **Integrate RAG** into agent's tool chain
4. **Build Streamlit UI** with search interface

---

✅ **RAG system ready!** Semantic search over forensic evidence is operational.

