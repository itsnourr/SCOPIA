# Forensic Crime Analysis Agent

An AI-powered forensic investigation system that helps law enforcement analyze crime scene evidence, rank suspects, and answer questions using advanced AI technologies including RAG (Retrieval-Augmented Generation), Vision AI, and hybrid scoring algorithms.

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Key Features](#key-features)
4. [Technology Stack](#technology-stack)
5. [Installation & Setup](#installation--setup)
6. [Configuration](#configuration)
7. [Usage Guide](#usage-guide)
8. [Tool Functionalities](#tool-functionalities)
9. [Development Guide](#development-guide)
10. [Testing](#testing)
11. [Security & Privacy](#security--privacy)
12. [Troubleshooting](#troubleshooting)
13. [Contributing](#contributing)

---

## Overview

The Forensic Crime Analysis Agent is a comprehensive AI-powered system designed for law enforcement and forensic investigators. It combines multiple advanced technologies to provide:

- **Intelligent Evidence Analysis**: Semantic search over case documents using RAG
- **Suspect Ranking**: Hybrid scoring algorithm with explainable AI
- **Vision AI**: Automatic image analysis with EXIF extraction
- **Timeline Analysis**: Automatic extraction and scoring of time-based events
- **Contradiction Detection**: Graph-based analysis of conflicting evidence
- **AI-Powered Q&A**: Natural language interface for case investigation
- **Secure Storage**: AES-256-CBC encryption for all evidence files

### Core Workflow

1. **Case Creation**: Create a case with title and description
2. **Evidence Upload**: Add images and text documents (witness statements, reports, etc.)
3. **Image Analysis**: Automatic encryption, EXIF extraction, and Vision AI captioning
4. **RAG Indexing**: Index all evidence in ChromaDB vector store with LLM-based relevance filtering
5. **Suspect Management**: Add suspects with profiles and metadata (vehicle, workplace, etc.)
6. **Evidence Correlation**: System scores suspects against evidence using hybrid algorithm
7. **AI Q&A**: Ask questions and get comprehensive answers based on all case evidence

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Streamlit UI (app/ui/app.py)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Case Mgmt    │  │ Evidence     │  │ Suspects     │  │ AI Q&A       │ │
│  │              │  │ Upload       │  │ Ranking      │  │ Interface    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │   Forensic   │ │   LangChain │ │    RAG     │
        │     LLM      │ │    Agent    │ │  Vector    │
        │              │ │             │ │   Store    │
        │ ForensicLLM │ │ create_agent│ │ ChromaDB   │
        │ class with   │ │ with tools  │ │ + Embed    │
        │ msg history  │ │ AIMessage   │ │            │
        └───────┬──────┘ └──────┬──────┘ └─────┬──────┘
                │               │               │
                └───────────────┼───────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼──────┐      ┌─────────▼─────────┐    ┌───────▼──────┐
│  PostgreSQL  │      │   ChromaDB        │    │   File      │
│  Database    │      │   Vector Store    │    │  Storage    │
│              │      │                   │    │             │
│ - Cases      │      │ - Document        │    │ - Encrypted │
│ - Suspects   │      │   Embeddings      │    │   Evidence  │
│ - Evidence   │      │ - Metadata        │    │   Files     │
│ - Chat       │      │ - Similarity      │    │             │
│   History    │      │   Search          │    │             │
│ - Memory     │      │                   │    │             │
└──────────────┘      └───────────────────┘    └──────────────┘
```

### Component Layers

#### 1. **Frontend Layer** (`app/ui/app.py`)
- **Technology**: Streamlit 1.29.0
- **Purpose**: Web-based dashboard for case management
- **Features**:
  - Case creation and selection
  - Evidence upload (images + text documents)
  - Suspect management
  - RAG index rebuilding
  - Evidence correlation and ranking
  - AI-powered Q&A interface
  - PDF export of rankings

#### 2. **Agent Layer** (`app/agent/`)
- **Technology**: LangChain + Multi-Provider LLM Support (OpenAI or Google Gemini)
- **Purpose**: Intelligent question answering with RAG integration
- **Components**:
  - `forensic_agent.py`: Main agent with ForensicLLM class, intent detection, and routing
  - `langchain_agent.py`: LangChain agent framework integration (PRIMARY execution engine)
  - `tools.py`: Custom LangChain tools (vector_search, get_case_summary, analyze_timeline_text)
  - `tool_runner.py`: P7-compliant tool execution wrapper
  - `llm_factory.py`: Unified LLM factory supporting OpenAI and Gemini providers

#### 3. **RAG Layer** (`app/rag/`)
- **Technology**: ChromaDB + sentence-transformers
- **Purpose**: Semantic search over evidence documents
- **Components**:
  - `vectorstore.py`: ChromaDB vector store management
  - `ingest.py`: Document ingestion from PostgreSQL to ChromaDB

#### 4. **Tools Layer** (`app/tools/`)
- **Purpose**: Specialized analysis tools
- **Components**:
  - `evidence_correlator.py`: Hybrid scoring algorithm for suspect ranking
  - `image_analyzer.py`: EXIF extraction + Vision AI captioning
  - `timeline_extractor.py`: LLM-based timeline event extraction
  - `timeline_engine.py`: Timeline building and scoring
  - `contradiction_graph.py`: Graph-based contradiction detection
  - `llm_filter.py`: LLM-based evidence relevance filtering
  - `llm_polarity.py`: Polarity classification for decisive evidence
  - `memory_extractor.py`: User memory extraction from messages

#### 5. **Database Layer** (`app/db/`)
- **Technology**: PostgreSQL + SQLAlchemy 2.0
- **Purpose**: Persistent storage of cases, suspects, evidence, and analysis results
- **Components**:
  - `models.py`: SQLAlchemy ORM models
  - `dao.py`: Data Access Object (CRUD operations)
  - `init_db.py`: Database initialization and schema management

#### 6. **Security Layer** (`app/security/`)
- **Technology**: AES-256-CBC encryption (cryptography + pycryptodome)
- **Purpose**: Encrypt evidence files at rest
- **Components**:
  - `crypto.py`: Original encryption implementation
  - `crypto_adapted.py`: Java-adapted implementation (recommended)

---

## Key Features

### 🧠 Intelligent Evidence Analysis

- **LLM-Based Relevance Filtering**: Evidence is filtered at ingestion time using configurable LLM (OpenAI or Gemini) to ensure only relevant documents enter the RAG index
- **Multi-Provider LLM Support**: Supports both OpenAI (GPT-4o-mini, GPT-4o) and Google Gemini (1.5/2.5 Flash, Pro) with automatic provider selection
- **Semantic Search**: RAG-powered evidence retrieval understands context, not just keywords
- **Dynamic Document Retrieval**: Automatically detects and uses ALL indexed evidence per case
- **Advanced Correlation**: 10+ accuracy improvements including source weighting, rare clue detection, and contradiction handling

### 🕐 Timeline Engine

- **Automatic Extraction**: LLM-based extraction of timeline events (arrivals, departures, sightings) from evidence
- **Chronological Timeline Building**: Automatic timeline construction with suspect matching
- **Proximity Scoring**: Timeline-based scoring based on proximity to murder time
- **Automatic Extraction**: Timeline events extracted during RAG indexing

### 🔗 Contradiction Detection

- **Graph-Based Analysis**: NetworkX graph representation of evidence relationships
- **LLM-Based Detection**: Intelligent detection of conflicting evidence between documents
- **Transparent Reasoning**: Reasoning trace for all contradictions
- **Penalty System**: Contradiction penalties applied to suspect scores

### 🎯 Polarity-Aware Decisive Evidence

- **Term-Specific Weights**: Each decisive term has its own forensic significance weight
  - DNA: 0.25 (highest), Fingerprints: 0.20, Weapons: 0.20, CCTV: 0.15, Footprints: 0.10
- **Multiple Sentence Aggregation**: Handles contradicting evidence by aggregating multiple sentences per term
- **Polarity Caching**: LLM classifications cached in database for consistency and speed
- **Improved Classification**: Enhanced prompt with detailed rules for better positive/negative/neutral differentiation

### 🧠 Reasoning Trace (Explainable AI)

- **Full Forensic Justification**: Complete breakdown of how each score component was calculated
- **Transparent Aggregation**: Shows positive/negative/neutral counts per term
- **Sorted by Impact**: Most significant factors first
- **Displayed in UI**: Included in formatted agent responses and PDF exports

### 🤖 AI-Powered Agent

- **Multi-Provider LLM Support**: Automatic provider selection (OpenAI or Gemini) based on configuration
- **LLM Factory Pattern**: Unified interface for creating LLM instances across all tools
- **RAG (Retrieval-Augmented Generation)**: Primary evidence retrieval system
- **LangChain Tools Integration**: Custom tools automatically called by the agent
- **Long-Term Memory**: Persistent user memory across sessions
- **Complete Chat History**: Full conversation context for intelligent responses
- **Ethical Guidelines**: All prompts include comprehensive ethical use guidelines

### 🖼️ Vision AI Analysis

- **Content Analysis**: Analyzes actual photo content using Gemini Vision AI (Gemini-specific feature)
- **Object Detection**: Identifies weapons, vehicles, people, evidence items
- **Text Recognition**: Reads visible text (signs, license plates, labels)
- **Cross-Checking**: Matches image content with suspect metadata
- **Note**: Vision AI requires Gemini API key (OpenAI can be used for all text-based LLM operations)

---

## Technology Stack

### Core Framework
- **Frontend**: Streamlit 1.29.0
- **LLM**: Multi-Provider Support (OpenAI GPT-4o-mini/GPT-4o or Google Gemini 1.5/2.5 Flash/Pro)
  - OpenAI via `langchain-openai` (recommended for demos - higher rate limits)
  - Google Gemini via `langchain-google-genai` (free tier available)
- **Vector DB**: ChromaDB 0.4.22 (semantic search and RAG)
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)

### Additional Libraries
- **Graph Analysis**: NetworkX 3.2.1 (contradiction detection)
- **Encryption**: AES-256-CBC (cryptography + pycryptodome)
- **Image Processing**: Pillow + piexif (EXIF extraction)
- **Data Visualization**: Plotly 5.18.0 (scoring breakdown charts)
- **PDF Generation**: reportlab 4.0.7 (ranking export)

---

## Installation & Setup

### Prerequisites

- **Python 3.11+**
- **PostgreSQL 14+**
- **LLM API Key** (choose one):
  - **OpenAI API Key** ([Get it here](https://platform.openai.com/api-keys)) - Recommended for demos
  - **Google Gemini API Key** ([Get it here](https://makersuite.google.com/app/apikey)) - Free tier available

### Step-by-Step Setup

#### 1. Clone and Navigate to Project

```bash
cd ForensicAgent
```

#### 2. Create Virtual Environment

```bash
python -m venv venv
```

#### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

#### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Configure Environment

**Windows:**
```bash
copy env.example .env
```

**Linux/Mac:**
```bash
cp env.example .env
```

#### 6. Edit `.env` File

Open `.env` and configure:

```bash
# LLM Provider Configuration (choose one or both - OpenAI takes priority)
# Option 1: OpenAI (Recommended for demos - higher rate limits)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Option 2: Google Gemini (Free tier available)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Required: PostgreSQL Database Connection
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/forensic_db

# Required: AES-256-CBC Encryption Key (32 bytes = 64 hex characters)
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
AES_MASTER_KEY=your_64_character_hex_key_here
```

#### 7. Create PostgreSQL Database

```bash
# Using createdb command
createdb forensic_db

# Or using psql
psql -U postgres -c "CREATE DATABASE forensic_db;"
```

#### 8. Create Data Directories

**Windows:**
```bash
mkdir data\encrypted data\chroma
```

**Linux/Mac:**
```bash
mkdir -p data/encrypted data/chroma
```

#### 9. Initialize Database Schema

```bash
python -m app.db.init_db
```

#### 10. Start the Application

```bash
streamlit run app/ui/app.py
```

The app will be available at `http://localhost:8501`

---

## Configuration

### Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key (takes priority if set) | `sk-...` | ⚠️ One required |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo` | ❌ No |
| `GEMINI_API_KEY` | Google Gemini API key | `AIza...` | ⚠️ One required |
| `GEMINI_MODEL` | Gemini model name | `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.5-flash` | ❌ No |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://user:pass@localhost:5432/db` | ✅ Yes |
| `AES_MASTER_KEY` | 32-byte hex encryption key | `a1b2c3d4...` (64 chars) | ✅ Yes |
| `FILES_DIR` | Encrypted files directory | `./data/encrypted` | ❌ No |
| `CHROMA_DIR` | ChromaDB storage directory | `./data/chroma` | ❌ No |
| `STREAMLIT_PORT` | Streamlit server port | `8501` | ❌ No |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ No |
| `MAX_UPLOAD_SIZE_MB` | Maximum file upload size | `100` | ❌ No |
| `MIN_CONFIDENCE_THRESHOLD` | Evidence correlation threshold | `0.65` | ❌ No |
| `ENABLE_ETHICAL_GUARDRAILS` | Enable ethical guardrails | `true` | ❌ No |
| `LANGCHAIN_VERBOSE` | LangChain verbose logging | `false` | ❌ No |
| `LANGCHAIN_TEMPERATURE` | LLM temperature | `0.1` | ❌ No |
| `CHROMA_COLLECTION_NAME` | ChromaDB collection name | `forensic_evidence` | ❌ No |

**Note**: You must configure at least one LLM provider (`OPENAI_API_KEY` or `GEMINI_API_KEY`). If both are set, OpenAI takes priority.

### Generate AES Encryption Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output (64 hexadecimal characters) to `AES_MASTER_KEY` in your `.env` file.

---

## Usage Guide

### Basic Workflow

1. **Create a Case**
   - Use the sidebar to create a new case
   - Enter case title and description

2. **Add Suspects**
   - Navigate to "Suspects" tab
   - Add suspect with name, profile, and metadata (vehicle, workplace, etc.)

3. **Upload Evidence**
   - **Images**: Upload via sidebar (automatically encrypted and analyzed)
   - **Text Documents**: Add witness statements, reports via "Evidence" tab

4. **Rebuild RAG Index**
   - Click "Rebuild Index" in sidebar
   - System indexes all evidence with LLM-based relevance filtering
   - Timeline events are automatically extracted

5. **Correlate Evidence**
   - Click "Correlate Evidence" in sidebar
   - View suspect rankings with detailed scoring breakdowns
   - Review reasoning trace for explainable AI

6. **Ask Questions**
   - Navigate to "Ask Agent" tab
   - Ask questions about the case
   - Agent retrieves relevant evidence and provides comprehensive answers

### Advanced Features

- **Long-Term Memory**: Tell the bot "my name is X" and it will remember across sessions
- **PDF Export**: Export complete rankings with detailed scoring breakdowns
- **Scoring Breakdown Charts**: Interactive visualization of score components
- **Tool Outputs**: View which tools were used with clickable code views

---

## Tool Functionalities

### Evidence Correlator (`app/tools/evidence_correlator.py`)

**Purpose**: Hybrid scoring algorithm for suspect ranking

**Key Features**:
- **Vector Similarity** (35% weight): Semantic matching with source-type weighting
- **Keyword Matching** (30% weight): Name mentions, metadata term matches
- **Decisive Evidence** (35% weight): Polarity-aware classification with term-specific weights
- **Timeline Scoring**: Proximity-based scoring from extracted timeline events
- **Contradiction Penalties**: Graph-based contradiction detection
- **Additional Boosts**: Vision AI matches, location triangulation, evidence coherence

**Usage**:
```python
from app.tools.evidence_correlator import correlate_and_persist

result = correlate_and_persist(case_id=1, query="Who is most likely responsible?")
for suspect in result["ranked"]:
    print(f"{suspect['suspect_name']}: {suspect['score']:.2f}")
```

### Image Analyzer (`app/tools/image_analyzer.py`)

**Purpose**: Image analysis with EXIF extraction and Vision AI

**Key Features**:
- **EXIF Extraction**: Datetime, GPS coordinates, camera model, dimensions
- **Vision AI Captioning**: Content analysis using Google Gemini Vision
- **In-Memory Decryption**: Decrypted bytes never written to disk
- **Comprehensive Captions**: Combines vision analysis with EXIF metadata

**Usage**:
```python
from app.tools.image_analyzer import analyze_image

result = analyze_image(image_id=1)
print(result['caption'])
print(result['exif'])
```

### Timeline Extractor (`app/tools/timeline_extractor.py`)

**Purpose**: LLM-based timeline event extraction

**Key Features**:
- **Event Types**: Arrival, departure, sightings, arguments, sounds, CCTV captures
- **Timestamp Parsing**: Normalizes timestamps to datetime objects
- **Suspect Matching**: Matches suspect names to suspect_ids
- **Automatic Extraction**: Runs during RAG indexing

**Usage**:
```python
from app.tools.timeline_extractor import extract_timeline_events

events = extract_timeline_events(text, doc_id="text_1", case_id=1)
for event in events:
    print(f"{event['event_type']} at {event['timestamp']}")
```

### Timeline Engine (`app/tools/timeline_engine.py`)

**Purpose**: Timeline building and scoring

**Key Features**:
- **Timeline Building**: Constructs chronological timeline from extracted events
- **Murder Time Extraction**: Extracts murder time from evidence
- **Proximity Scoring**: Scores based on proximity to murder window
  - Within 20 minutes: +0.15
  - Within 1 hour: +0.05
  - 1-3 hours away: -0.05
  - >3 hours away: -0.10
  - No timeline presence: -0.15

### Contradiction Graph (`app/tools/contradiction_graph.py`)

**Purpose**: Graph-based contradiction detection

**Key Features**:
- **Graph Building**: NetworkX graph representation of evidence relationships
- **LLM-Based Detection**: Detects contradictions between evidence pairs
- **Penalty Calculation**: -0.05 per contradiction (capped at -0.25)
- **Transparent Reasoning**: Reasoning trace for all contradictions

### LLM Filter (`app/tools/llm_filter.py`)

**Purpose**: LLM-based evidence relevance filtering

**Key Features**:
- **Relevance Classification**: Uses LLM to classify evidence relevance
- **Ingestion-Time Filtering**: Applied during RAG indexing
- **Requirements**: Person/vehicle/object + action/movement + time/location context
- **Keeps Database Clean**: Filters out generic scenery and irrelevant content

### LLM Polarity (`app/tools/llm_polarity.py`)

**Purpose**: Polarity classification for decisive evidence

**Key Features**:
- **Sentence Classification**: Classifies sentences with suspect name + decisive term
- **Polarity Types**: Positive, negative, or neutral
- **Caching**: LLM classifications cached in database
- **Deterministic**: Temperature 0.0 for reproducible results

### Memory Extractor (`app/tools/memory_extractor.py`)

**Purpose**: User memory extraction from messages

**Key Features**:
- **Regex Patterns**: Fast extraction using regex (name, location, birthday, etc.)
- **LLM Fallback**: LLM extraction for general cases
- **Personal Info Only**: Only extracts user personal info, not case evidence
- **Deterministic**: Temperature 0.0 for consistent results

### LangChain Tools (`app/agent/tools.py`)

**Purpose**: Custom tools for the LangChain agent

**Available Tools**:

1. **`vector_search(query, case_id, k=10)`**
   - Performs semantic search over case evidence using RAG
   - Automatically called by agent for evidence retrieval
   - Returns formatted evidence documents with citations

2. **`get_case_summary(case_id)`**
   - Returns comprehensive structured case overview
   - Triggered by: "summary", "overview", "case info", "summarize this case", "summarize the case"
   - Returns: 
     - Case title, description, creation date
     - Suspects with profiles and metadata
     - Evidence breakdown by type (witness statements, forensic reports, etc.)
     - Key findings from evidence (using RAG to retrieve top relevant documents)
     - Timeline overview (top 5 events)
     - Latest correlation results (top 3 suspects with scores)
   - The LLM enhances this tool output with specific evidence details and citations

3. **`analyze_timeline_text(text, case_id)`**
   - Extracts timeline events from arbitrary text
   - Triggered by: "extract timeline", "analyze timeline"
   - Returns: Event types, timestamps, confidence scores

---

## Development Guide

### Project Structure

```
ForensicAgent/
├── app/
│   ├── agent/          # LangChain agent orchestration
│   │   ├── forensic_agent.py  # Main agent with RAG integration
│   │   ├── tools.py            # LangChain tools
│   │   ├── langchain_agent.py  # LangChain agent framework
│   │   └── tool_runner.py      # Tool execution wrapper
│   ├── tools/          # Custom analysis tools
│   │   ├── evidence_correlator.py
│   │   ├── image_analyzer.py
│   │   ├── timeline_extractor.py
│   │   ├── timeline_engine.py
│   │   ├── contradiction_graph.py
│   │   ├── llm_filter.py
│   │   ├── llm_polarity.py
│   │   └── memory_extractor.py
│   ├── rag/            # RAG implementation
│   │   ├── vectorstore.py
│   │   └── ingest.py
│   ├── ui/             # Streamlit interface
│   │   └── app.py
│   ├── security/       # AES encryption
│   │   ├── crypto.py
│   │   └── crypto_adapted.py
│   ├── db/             # Database models & management
│   │   ├── models.py
│   │   ├── dao.py
│   │   └── init_db.py
│   └── tests/          # Test suite
├── data/
│   ├── encrypted/      # Encrypted evidence files
│   └── chroma/         # ChromaDB vector store
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── env.example         # Environment template
└── README.md           # This file
```

### Development Workflow

#### 1. Setting Up Development Environment

```bash
# Clone repository
git clone <repository-url>
cd ForensicAgent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install black flake8 mypy pytest pytest-cov

# Configure environment
cp env.example .env
# Edit .env with your credentials

# Initialize database
python -m app.db.init_db
```

#### 2. Code Style

**Formatting**: Use `black` with line length 100
```bash
black app --line-length=100
```

**Linting**: Use `flake8` and `mypy`
```bash
flake8 app --max-line-length=100 --ignore=E203,W503
mypy app --ignore-missing-imports
```

#### 3. Adding New Features

**Adding a New Tool**:

1. Create tool file in `app/tools/`
2. Implement tool functions with proper error handling
3. Add tests in `app/tests/`
4. Update documentation

**Adding a New LangChain Tool**:

1. Add tool function in `app/agent/tools.py`
2. Use `@tool` decorator
3. Register tool in `app/agent/langchain_agent.py`
4. Update agent prompts if needed

**Adding a New Database Model**:

1. Add model class in `app/db/models.py`
2. Add DAO functions in `app/db/dao.py`
3. Run database migration: `python -m app.db.init_db`
4. Add tests

#### 4. Database Migrations

Currently, the system uses `init_db.py` for schema management. For production, consider using Alembic:

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

#### 5. Testing

**Run all tests**:
```bash
pytest app/tests/ -v
```

**Run with coverage**:
```bash
pytest app/tests/ -v --cov=app --cov-report=html
```

**Run specific test file**:
```bash
pytest app/tests/test_agent.py -v
```

#### 6. Debugging

**Enable verbose logging**:
```bash
# In .env
LOG_LEVEL=DEBUG
LANGCHAIN_VERBOSE=true
```

**Check database connection**:
```bash
python -c "from app.db.init_db import test_connection, get_engine; test_connection(get_engine())"
```

**Validate configuration**:
```bash
python config.py
```

### Development Best Practices

1. **Error Handling**: Always use try-except blocks with proper logging
2. **Type Hints**: Use type hints for all function signatures
3. **Documentation**: Add docstrings to all functions and classes
4. **Testing**: Write tests for new features
5. **Security**: Never log sensitive data (API keys, encryption keys)
6. **Ethical Guidelines**: All LLM prompts must include ethical guidelines
7. **Code Review**: Review code before merging to main branch

---

## Testing

### Test Structure

Tests are located in `app/tests/`:

- `test_agent.py`: Agent functionality tests
- `test_correlator.py`: Evidence correlator tests
- `test_crypto.py`: Encryption tests
- `test_db.py`: Database operation tests
- `test_image_analyzer.py`: Image analysis tests
- `test_rag.py`: RAG system tests

### Running Tests

**Run all tests**:
```bash
pytest app/tests/ -v
```

**Run with coverage**:
```bash
pytest app/tests/ -v --cov=app --cov-report=html --cov-report=term
```

**Run specific test file**:
```bash
pytest app/tests/test_agent.py -v
```

**Run specific test**:
```bash
pytest app/tests/test_agent.py::test_answer_question -v
```

### Test Status

**Core Components**: Fully tested and passing
- ✅ Agent (Core AI): 32/32 (100%)
- ✅ Evidence Correlator: 10/10 (100%)
- ✅ Crypto Adapted: 11/11 (100%)

**Note**: Some test modules require additional mocking for database and image analysis components. Core functionality (agent, correlator, encryption) is fully tested and working.

---

## Security & Privacy

### Encryption at Rest

- **Algorithm**: AES-256-CBC
- **Key Management**: 32-byte master key stored in `.env` (64 hex characters)
- **IV Generation**: Random 16-byte IV per file
- **Integrity**: HMAC-SHA256 for file integrity verification
- **Storage**: Encrypted files stored in `data/encrypted/` directory
- **Decryption**: Only happens in-memory during analysis/retrieval

### Database Security

- **Connection**: PostgreSQL with connection pooling
- **Credentials**: Stored in `.env` file (never hardcoded)
- **Schema**: SQLAlchemy ORM with proper relationships
- **Cascade Deletes**: Deleting case deletes all related records

### API Key Management

- **Gemini API Key**: Stored in `.env` file
- **Validation**: Checked at startup
- **Error Handling**: Graceful fallbacks if API unavailable

### Ethical Guardrails

- **System Prompts**: All LLM prompts include ethical guidelines
- **Insufficient Evidence**: System refuses to speculate
- **Presumption of Innocence**: All analysis marked as "decision support only"
- **Transparency**: Reasoning trace shows how scores were calculated

---

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Verify DATABASE_URL in .env
# Windows:
type .env | findstr DATABASE_URL
# Linux/Mac:
cat .env | grep DATABASE_URL
```

### Module Not Found

```bash
# Ensure virtual environment is activated
# Windows:
where python
# Linux/Mac:
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Port Already in Use

```bash
# Change port in .env
STREAMLIT_PORT=8502

# Or specify manually
streamlit run app/ui/app.py --server.port=8502
```

### ChromaDB Issues

```bash
# Reset ChromaDB (WARNING: deletes all vector data)
rm -rf data/chroma/*
python -m app.rag.vectorstore  # Reinitialize
```

### Image Analysis Errors

- **Decryption Errors**: Check `AES_MASTER_KEY` in `.env`
- **Vision AI Errors**: Check `GEMINI_API_KEY` in `.env`
- **EXIF Errors**: Non-critical, analysis continues without EXIF

### RAG Indexing Issues

- **No Documents Found**: Ensure evidence is added to case
- **LLM Filtering Fails**: Check `GEMINI_API_KEY` and API limits
- **Slow Indexing**: Reduce number of documents or increase API rate limits

---

## Contributing

### Contribution Guidelines

1. **Fork the Repository**: Create your own fork
2. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
3. **Follow Code Style**: Use `black` for formatting, `flake8` for linting
4. **Write Tests**: Add tests for new features
5. **Update Documentation**: Update README and docstrings
6. **Commit Changes**: Use descriptive commit messages
7. **Push to Branch**: `git push origin feature/your-feature-name`
8. **Create Pull Request**: Submit PR with description

### Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Maintain ethical standards
- Follow security best practices

---

## License

This is a forensic analysis tool for law enforcement and legal professionals. Use responsibly and ethically.

---

## Support & Documentation

### Additional Documentation

- **[Complete System Explanation](COMPLETE_SYSTEM_EXPLANATION.md)**: Comprehensive technical documentation covering architecture, design, code explanations, integration points, security, performance, deployment, and troubleshooting
- **[Testing Guide](TESTING_GUIDE.md)**: Step-by-step manual testing tutorial
- **[Tools Documentation](app/tools/README.md)**: Evidence Correlator and Image Analyzer guides

### Module Documentation

- `app/tools/README.md` - Custom tool development
- `app/security/README.md` - Security best practices
- `app/ui/README.md` - UI features and customization
- `app/rag/README.md` - RAG system documentation
- `app/db/README.md` - Database schema and operations

> **Note**: Agent configuration, prompts, and architecture are comprehensively covered in [COMPLETE_SYSTEM_EXPLANATION.md](COMPLETE_SYSTEM_EXPLANATION.md).

---

## Contact & Team

Built by a 3-person team specializing in AI-powered forensic systems.

For questions, issues, or contributions, please open an issue on the repository.

