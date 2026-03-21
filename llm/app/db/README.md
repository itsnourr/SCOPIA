# Database Layer Documentation

Complete PostgreSQL database implementation for Forensic Crime Analysis Agent using SQLAlchemy 2.x.

## 📁 Files

| File | Purpose |
|------|---------|
| `models.py` | ORM models (Case, Suspect, TextDocument, Image, AnalysisResult) |
| `init_db.py` | Database initialization and schema creation |
| `dao.py` | Data Access Object with CRUD operations |
| `__init__.py` | Package exports |

## 🗃️ Database Schema

### Tables

```
cases
  ├── id (PK)
  ├── title
  ├── description
  └── created_at

suspects
  ├── id (PK)
  ├── case_id (FK → cases.id)
  ├── name
  ├── profile_text
  ├── metadata_json
  └── created_at

text_documents
  ├── id (PK)
  ├── case_id (FK → cases.id)
  ├── source_type
  ├── title
  ├── content
  └── created_at

images
  ├── id (PK)
  ├── case_id (FK → cases.id)
  ├── filename
  ├── file_path (UNIQUE)
  ├── iv_hex
  ├── sha256_hex
  ├── exif_json
  ├── caption_text
  └── created_at

analysis_results
  ├── id (PK)
  ├── case_id (FK → cases.id)
  ├── suspect_id (FK → suspects.id)
  ├── score_float
  ├── matched_clues_json
  └── run_at
```

### Relationships

- **Case** → Suspects (one-to-many, cascade delete)
- **Case** → TextDocuments (one-to-many, cascade delete)
- **Case** → Images (one-to-many, cascade delete)
- **Case** → AnalysisResults (one-to-many, cascade delete)
- **Suspect** → AnalysisResults (one-to-many, cascade delete)

## 🚀 Quick Start

### 1. Initialize Database

```bash
# Initialize database schema
python -m app.db.init_db

# Reset database (WARNING: deletes all data)
python -m app.db.init_db --reset
```

### 2. Basic Usage

```python
from app.db import (
    init_db,
    add_case,
    add_suspect,
    add_text,
    add_image,
    get_case_data
)

# Initialize database
init_db()

# Create a case
case = add_case(
    title="Jewelry Heist",
    description="Investigation into diamond theft"
)

# Add a suspect
suspect = add_suspect(
    case_id=case.id,
    name="John Doe",
    profile_text="Known burglar with history",
    metadata_json={"age": 35, "alibi": "None"}
)

# Add text evidence
text = add_text(
    case_id=case.id,
    source_type="witness",
    title="Witness Statement",
    content="I saw a suspicious person..."
)

# Add image evidence
image = add_image(
    case_id=case.id,
    filename="evidence.jpg",
    file_path="/data/encrypted/case1_img1.enc",
    iv_hex="0123456789abcdef0123456789abcdef",
    sha256_hex="a" * 64
)

# Get complete case data
data = get_case_data(case.id)
```

## 📚 DAO Functions

### Case Operations

```python
# Create
case = add_case(title, description)

# Read
case = get_case(case_id)
cases = get_all_cases()
data = get_case_data(case_id)  # Complete with relationships

# Delete
success = delete_case(case_id)
```

### Suspect Operations

```python
# Create
suspect = add_suspect(case_id, name, profile_text, metadata_json)

# Read
suspects = get_suspects_by_case(case_id)
```

### Text Document Operations

```python
# Create
text = add_text(case_id, source_type, title, content)

# Read
texts = get_texts_by_case(case_id)
```

### Image Operations

```python
# Create
image = add_image(case_id, filename, file_path, iv_hex, sha256_hex)

# Update with AI analysis
success = update_image_analysis(image_id, exif_json, caption_text)

# Read
images = get_images_by_case(case_id)
```

### Analysis Results

```python
# Save results from Evidence Correlator tool
results = [
    {
        "suspect_id": 1,
        "score": 0.85,
        "matched_clues": {"location": "Near scene", "motive": "Financial"}
    },
    {
        "suspect_id": 2,
        "score": 0.42,
        "matched_clues": {"alibi": "Confirmed"}
    }
]
save_analysis_results(case_id, results)

# Read
results = get_analysis_results(case_id)  # Ordered by score DESC
```

## 🧪 Testing

Run the test suite:

```bash
# Run all database tests
pytest app/tests/test_db.py -v

# Run with coverage
pytest app/tests/test_db.py -v --cov=app.db

# Run specific test
pytest app/tests/test_db.py::test_add_case -v
```

## 🔧 Session Management

All DAO functions use context-managed sessions that automatically:
- Commit on success
- Rollback on error
- Close after use

For custom queries, use the session context manager:

```python
from app.db import get_db_session

with get_db_session() as session:
    # Your queries here
    case = session.query(Case).filter(Case.id == 1).first()
    # Automatically commits and closes
```

## 🛡️ Error Handling

All DAO functions:
- Return `None` on failure (for single objects)
- Return empty lists on failure (for collections)
- Log errors with details
- Handle `IntegrityError` (FK violations, unique constraints)
- Handle `SQLAlchemyError` (general DB errors)

## 🔍 Example: Complete Workflow

See `example_db_usage.py` for a complete example showing:
1. Database initialization
2. Creating cases with multiple suspects
3. Adding text and image evidence
4. Updating images with AI analysis
5. Saving analysis results
6. Retrieving complete case data

Run it with:
```bash
python example_db_usage.py
```

## 📝 Type Hints

All functions use modern Python type hints:

```python
def add_case(title: str, description: str) -> Optional[Case]: ...
def get_suspects_by_case(case_id: int) -> List[Suspect]: ...
def get_case_data(case_id: int) -> Optional[Dict[str, Any]]: ...
```

## 🔐 Security Notes

- **Images**: Only metadata stored in DB, encrypted files stored on disk
- **IV & Hash**: Initialization vector and SHA-256 hash stored as hex strings
- **JSON Fields**: Use PostgreSQL JSON type for flexible metadata
- **Cascade Delete**: Deleting a case removes all related evidence

## 🚨 Common Issues

### "Cannot connect to database"
- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running
- Verify credentials and database exists

### "Table does not exist"
- Run: `python -m app.db.init_db`

### Foreign key violations
- Ensure parent records exist before creating children
- Use `get_case()` to verify case exists before adding evidence

## 🔄 Next Steps

After setting up the database:
1. Build encryption layer: `app/security/encryption.py`
2. Create Image Analyzer tool: `app/tools/image_analyzer.py`
3. Build Evidence Correlator: `app/tools/evidence_correlator.py`
4. Set up ChromaDB RAG: `app/rag/vector_store.py`

