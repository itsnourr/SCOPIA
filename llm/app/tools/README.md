# Custom Tools for Forensic Analysis

Custom LangChain-compatible tools for analyzing forensic evidence.

---

## 🔧 Available Tools

### ✅ **Image Analyzer**

Analyzes evidence images by:
- Decrypting encrypted images (in-memory only)
- Extracting EXIF metadata (datetime, GPS, camera)
- Generating descriptive captions with Vision AI
- Updating database with results

**Location:** `app/tools/image_analyzer.py`

---

### ✅ **Evidence Correlator**

Ranks suspects by how well case evidence supports them using advanced hybrid scoring:
- **Vector similarity** (semantic matching with source weighting)
- **Keyword matching** (name mentions, decisive terms, metadata)
- **Rule-based boosts** (forensic evidence like DNA, fingerprints)
- **Vision AI cross-checking** (vehicle, clothing, object matches)
- **Evidence coherence** (consistency between evidence documents)
- **Location triangulation** (workplace, neighborhood matches)
- **Cross-evidence graph reasoning** (weighted connection counting)
- **Rare clue weighting** (confession, DNA get extra weight)
- **Contradiction detection** (vehicle type/color mismatches)

**Location:** `app/tools/evidence_correlator.py`

---

## 🖼️ Image Analyzer Tool

### Quick Start

```python
from app.tools import analyze_image

# Analyze a single image
result = analyze_image(image_id=1)

if result['success']:
    print(f"Caption: {result['caption']}")
    print(f"EXIF: {result['exif']}")
else:
    print(f"Error: {result['error']}")
```

### Functions

#### `analyze_image(image_id: int)`

Complete workflow: decrypt → extract EXIF → generate caption → update DB

**Args:**
- `image_id`: Database ID of image to analyze

**Returns:**
```python
{
    'image_id': 1,
    'filename': 'evidence.jpg',
    'caption': 'Evidence photo taken on 2024-03-15...',
    'exif': {
        'datetime': '2024-03-15 14:23:10',
        'camera': 'iPhone 14 Pro',
        'gps': {'lat': 40.7128, 'lon': -74.0060},
        'width': 1920,
        'height': 1080,
        'raw': {...}
    },
    'success': True,
    'error': None
}
```

#### `extract_exif(file_path, key_hex, iv_hex)`

Decrypt and extract EXIF metadata

**Args:**
- `file_path`: Path to encrypted image
- `key_hex`: Encryption key (hex)
- `iv_hex`: IV (hex)

**Returns:**
```python
{
    'datetime': '2024-03-15 14:23:10',
    'camera': 'iPhone 14 Pro',
    'gps': {'lat': 40.7128, 'lon': -74.0060},
    'width': 1920,
    'height': 1080,
    'raw': {...}  # Full EXIF data
}
```

#### `generate_caption(filename, exif)`

Generate descriptive caption from EXIF data

**Args:**
- `filename`: Original filename
- `exif`: EXIF data dict (or None)

**Returns:**
```python
"Evidence photo taken on 2024-03-15 14:23:10 with iPhone 14 Pro at location 40.7128°N, 74.0060°W"
```

#### `batch_analyze_images(case_id)`

Analyze all images in a case

**Args:**
- `case_id`: Case ID

**Returns:**
```python
{
    'total': 5,
    'analyzed': 5,
    'failed': 0,
    'results': [...]
}
```

---

## 📋 Complete Workflow

### 1. Upload Image

```python
from app.security import get_crypto_service
from app.db import add_image

# Encrypt and save image
crypto = get_crypto_service()
metadata = crypto.encrypt_file("evidence.jpg", image_bytes)

# Store in database
image = add_image(
    case_id=1,
    filename="evidence.jpg",
    file_path=metadata["file_path"],
    iv_hex=iv_hex,
    sha256_hex=sha256_hex
)
```

### 2. Analyze Image

```python
from app.tools import analyze_image

# Extract EXIF and generate caption
result = analyze_image(image.id)

print(f"Caption: {result['caption']}")
# "Evidence photo taken on 2024-03-15..."
```

### 3. Index for RAG

```python
from app.rag import build_case_index

# Index caption for semantic search
build_case_index(case_id=1)
```

### 4. Search Evidence

```python
from app.rag import query_documents

# Search using image captions
results = query_documents("photo taken in march", case_id=1)
```

---

## 🔐 Security Features

### In-Memory Processing

✅ **Never writes plaintext to disk**
- Decrypted image bytes kept in memory only
- Processed and discarded immediately
- Only encrypted files stored on disk

### Error Handling

- **Wrong key/IV**: Raises `DecryptionError`, no DB update
- **Corrupted file**: Fails gracefully, no DB update
- **Missing EXIF**: Generates generic caption, continues
- **Invalid image**: Returns error, no crash

### Robustness

- Works with images with/without EXIF
- Handles missing GPS, camera, datetime
- Supports multiple EXIF formats (Pillow, exifread)
- Graceful degradation on errors

---

## 🧪 Testing

```bash
# Run all image analyzer tests
pytest app/tests/test_image_analyzer.py -v

# Run specific test
pytest app/tests/test_image_analyzer.py::test_analyze_image_success -v

# Run with coverage
pytest app/tests/test_image_analyzer.py --cov=app.tools
```

### Test Coverage

- ✅ EXIF extraction (with/without metadata)
- ✅ Caption generation (various EXIF combinations)
- ✅ Complete analysis workflow
- ✅ Database integration
- ✅ Error handling (wrong key, wrong IV, corrupted data)
- ✅ Batch analysis
- ✅ Security (no plaintext persistence)
- ✅ Edge cases (large images, special characters)

---

## 📊 EXIF Data Extracted

| Field | Description | Example |
|-------|-------------|---------|
| `datetime` | Capture timestamp | `2024-03-15 14:23:10` |
| `camera` | Camera model | `iPhone 14 Pro` |
| `gps` | GPS coordinates | `{'lat': 40.7128, 'lon': -74.0060}` |
| `width` | Image width (px) | `1920` |
| `height` | Image height (px) | `1080` |
| `raw` | All EXIF tags | `{...}` |

### GPS Format

```python
{
    'lat': 40.7128,   # Decimal degrees, negative = South
    'lon': -74.0060   # Decimal degrees, negative = West
}
```

---

## 🎯 Caption Examples

### With Full EXIF

```
Evidence photo taken on 2024-03-15 14:23:10 with iPhone 14 Pro at location 40.7128°N, 74.0060°W. Image dimensions: 1920x1080 pixels.
```

### With Partial EXIF

```
Evidence photo taken on 2024-03-15 14:23:10. Image dimensions: 800x600 pixels.
```

### Without EXIF

```
Evidence photo: crime scene 001 (no metadata available).
```

---

## 🔗 Integration with RAG

After analyzing images, captions are indexed for semantic search:

```python
# 1. Analyze images
from app.tools import batch_analyze_images
batch_analyze_images(case_id=1)

# 2. Build RAG index (includes image captions)
from app.rag import build_case_index
build_case_index(case_id=1)

# 3. Search across all evidence (texts + images)
from app.rag import query_documents
results = query_documents("iPhone photo taken in march", case_id=1)

# Results include both text documents and image captions
for doc in results:
    print(f"{doc['metadata']['source_type']}: {doc['text'][:100]}")
# Output:
# image: Evidence photo taken on 2024-03-15 with iPhone...
# witness: I saw someone taking photos with their phone...
```

---

## ⚠️ Important Notes

1. **Decryption Key**: Uses `Config.AES_MASTER_KEY` from environment
2. **Database Dependency**: Requires image record with `file_path` and `iv_hex`
3. **Memory Usage**: Large images (>10MB) kept in memory during processing
4. **EXIF Formats**: Supports both Pillow and exifread formats
5. **GPS Precision**: Rounded to 6 decimal places (~10cm accuracy)
6. **Caption Length**: Typically 50-200 characters

---

## 🐛 Troubleshooting

### "DecryptionError: incorrect key or IV"

- Check `AES_MASTER_KEY` in `.env` matches encryption key
- Verify `iv_hex` in database is correct
- Ensure file hasn't been corrupted

### "No EXIF data found"

- Some images don't have EXIF (e.g., screenshots)
- Tool generates generic caption automatically
- This is normal and not an error

### "Image not found in database"

- Verify image record exists: `get_images_by_case(case_id)`
- Check `image_id` is correct

### High memory usage

- Large images (4K+) use significant RAM during processing
- Memory is freed after analysis completes
- For batch processing, consider chunking

---

---

## 🎯 Evidence Correlator Tool

### Quick Start

```python
from app.tools.evidence_correlator import correlate_and_persist

# Correlate evidence with suspects
result = correlate_and_persist(case_id=1, query="Who is most likely responsible?")

# View rankings
for suspect in result["ranked"]:
    print(f"{suspect['suspect_name']}: {suspect['score']:.2f}")
    print(f"  Clues: {', '.join(suspect['matched_clues'])}")
```

### Functions

#### `correlate_and_persist(case_id, query=None, k=8)`

High-level entry point: extract evidence, score suspects, persist results.

**Args:**
- `case_id`: Case ID to analyze
- `query`: Optional search query (uses default if None)
- `k`: Number of evidence documents to retrieve

**Returns:**
```python
{
    'case_id': 1,
    'query': 'most incriminating evidence',
    'docs_used': 8,
    'ranked': [
        {
            'suspect_id': 1,
            'suspect_name': 'John Doe',
            'score': 0.85,
            'matched_clues': [
                'Name mentioned 3 time(s) in evidence',
                'Decisive evidence: fingerprints, dna',
                'Vision AI match (+0.10)',
                'Multiple evidence connections (+0.12)'
            ],
            'components': {
                'base_sim': 0.72,
                'keyword_score': 0.65,
                'decisive_bonus': 0.25
            },
            'contributing_docs': [...]
        },
        ...
    ],
    'persisted': True
}
```

#### `score_suspects(case_id, evidence_docs)`

Score all suspects for a case based on evidence documents.

#### `extract_evidence_context(case_id, query=None, k=8)`

Use RAG to fetch top-k most relevant documents for case.

---

### 🧠 Advanced Scoring Features

#### 1. **Source-Type Weighting**

Different evidence sources carry different confidence levels:

| Source Type | Weight | Description |
|------------|-------|-------------|
| `forensic` | 1.0 | Lab reports, DNA analysis (highest confidence) |
| `image` | 0.8 | Vision AI analyzed images (medium-high) |
| `report` | 0.7 | Official reports (medium) |
| `witness` | 0.5 | Witness statements (low, high noise) |
| `unknown` | 0.4 | Unknown sources (lowest) |

#### 2. **Token-Based Proximity Detection**

Decisive evidence (fingerprints, DNA) is only attributed to suspects if found within **5 words** of their name or metadata, ensuring accurate attribution.

#### 3. **Metadata Reasoning**

Strong signals when multiple metadata fields appear together:
- **Vehicle + Location + Decisive Evidence**: +0.20 boost
- **Vehicle + Location**: +0.20 boost
- **Vehicle only**: +0.15 boost
- **Location only**: +0.10 boost

#### 4. **Evidence Coherence**

Measures consistency between evidence documents:
- **High coherence (>0.6)**: Evidence agrees → +0.04 boost
- **Low coherence (<0.3)**: Evidence contradicts → -0.03 penalty

#### 5. **Vision AI Cross-Checking**

Matches Vision AI captions with suspect metadata:
- **Vehicle match**: +0.10 boost
- **Clothing match**: +0.08 boost
- **Object match** (weapons, bags): +0.05 boost

#### 6. **Location Triangulation**

Boosts when evidence mentions suspect's known locations:
- **Workplace mentioned**: +0.10 boost
- **Neighborhood mentioned**: +0.10 boost
- **Multiple locations**: Up to +0.15 boost

#### 7. **Cross-Evidence Graph Reasoning**

Weighted connection counting:
- **Name mention**: 1.0 weight (strongest)
- **Metadata match**: 0.7 weight (medium)
- **Decisive evidence**: 1.3 weight (strongest)
- **Final boost**: Up to +0.15 based on weighted connections

#### 8. **Rare Clue Weighting**

Extremely strong evidence gets extra weight:

| Term | Weight | Description |
|------|--------|-------------|
| `confession` | 0.20 | Extremely rare, very strong |
| `admitted` | 0.15 | Very strong |
| `dna` | 0.15 | Strong forensic evidence |
| `fingerprints` | 0.10 | Strong forensic evidence |
| `video` | 0.08 | Strong visual evidence |
| `cctv` | 0.08 | Strong visual evidence |

#### 9. **Improved Contradiction Detection**

Detects vehicle mismatches:
- **Type mismatch** (e.g., "truck" vs "sedan"): -0.15 penalty
- **Color mismatch** (e.g., "blue" vs "red"): -0.10 penalty
- **Multiple contradictions**: Additional scaled penalty

#### 10. **Negative Evidence Handling**

- **Suspect not mentioned anywhere**: Score halved if no name match and weak keyword score
- **Weak evidence decay**: Evidence with low RAG relevance (<0.3) gets reduced weight
- **Contradiction penalties**: Scaled penalties for multiple contradictions

---

### 📊 Scoring Formula

```
final_score = 
    (W_SIM * base_sim) +           # 50% - Vector similarity
    (W_KW * keyword_score) +       # 25% - Keyword matching
    decisive_bonus +               # 25% - Decisive evidence (rare clues weighted)
    coherence_boost +               # Up to +0.04
    vision_boost +                  # Up to +0.15
    timeline_boost +                # Up to +0.15 (future)
    graph_boost +                   # Up to +0.15
    location_boost -                # Up to +0.15
    contradiction_penalties         # Up to -0.15

# Normalized to [0, 1.0]
final_score = min(final_score, 1.0)
```

---

### 🔍 Scoring Components

Each suspect result includes:

- **`score`**: Final hybrid score [0, 1.0]
- **`matched_clues`**: List of evidence clues found
- **`components`**: Breakdown of scoring components
  - `base_sim`: Vector similarity score
  - `keyword_score`: Keyword matching score
  - `decisive_bonus`: Decisive evidence bonus
- **`contributing_docs`**: Top 3 evidence documents that contributed most

---

### 📝 Example Output

```python
{
    'suspect_name': 'John Doe',
    'score': 0.85,
    'matched_clues': [
        'Name mentioned 3 time(s) in evidence',
        'Decisive evidence: fingerprints, dna',
        'Vision AI match (+0.10)',
        'Multiple evidence connections (+0.12)',
        'High profile similarity (0.72)'
    ],
    'components': {
        'base_sim': 0.72,
        'keyword_score': 0.65,
        'decisive_bonus': 0.25
    },
    'contributing_docs': [
        {'doc_id': 'T1', 'title': 'Forensic Report', 'score': 0.88},
        {'doc_id': 'I1', 'title': 'Image: evidence.jpg', 'score': 0.82},
        {'doc_id': 'T2', 'title': 'Witness Statement', 'score': 0.75}
    ]
}
```

---

### 🧪 Testing

```bash
# Run all correlator tests
pytest app/tests/test_correlator.py -v

# Run specific test
pytest app/tests/test_correlator.py::test_score_suspects_structure_and_sorting -v
```

---

### ⚙️ Configuration

Scoring weights are configurable constants at the top of `evidence_correlator.py`:

```python
W_SIM = 0.50        # Vector similarity weight
W_KW = 0.25         # Keyword matching weight
W_DECISIVE = 0.25   # Decisive evidence weight

WEIGHTS_BY_SOURCE = {
    "forensic": 1.0,
    "image": 0.8,
    "report": 0.7,
    "witness": 0.5,
    ...
}

RARE_TERMS = {
    'confession': 0.20,
    'dna': 0.15,
    ...
}
```

---

## 🔄 Next Steps

After implementing tools:

1. ✅ **Image Analyzer** - Complete
2. ✅ **Evidence Correlator** - Complete with advanced features
3. ✅ **LangChain Agent** - Integrates tools with Gemini Pro
4. ✅ **Streamlit UI** - Full analysis interface

---

✅ **All tools ready!** Analyze evidence images and correlate suspects with advanced AI-powered scoring.

