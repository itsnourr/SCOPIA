# Streamlit UI Module

Interactive web dashboard for the Forensic Crime Analysis Agent.

---

## 🚀 Quick Start

### Run the Application

```bash
# From project root
streamlit run app/ui/app.py

# Or use Makefile
make run
```

The app will start at `http://localhost:8501`

---

## 📋 Features

### 1. **Case Management**
- Select from existing cases
- Create new cases with title and description
- View case statistics and activity timeline

### 2. **Evidence Upload**
- Upload images (JPG, PNG, GIF, BMP)
- Automatic AES-256-CBC encryption
- Automatic EXIF extraction
- AI-generated captions
- File size validation (configurable limit)

### 3. **RAG Vector Index**
- Rebuild semantic search index
- View indexed document count
- Automatic indexing of image captions and text evidence

### 4. **Suspect Correlation**
- One-click evidence correlation
- Interactive bar charts showing suspect scores
- Detailed breakdowns of:
  - Vector similarity scores
  - Keyword matches
  - Matched clues
  - Contributing evidence documents

### 5. **AI Agent Q&A**
- Natural language queries about case evidence
- Automatic intent detection (ranking vs general Q&A)
- Answers with citations
- Conversation history
- Ethical guardrails built-in

---

## 🎨 UI Components

### Sidebar
- **Case Selection**: Dropdown with all cases
- **Upload Evidence**: File uploader with encryption
- **Rebuild Index**: RAG indexing button
- **Correlate Suspects**: Run evidence correlation
- **Create Case**: Quick case creation form

### Main Tabs

#### 📊 Overview
- Case statistics (suspects, documents, images, analyses)
- Recent activity timeline
- Quick metrics

#### 🔍 Evidence
- List of all uploaded evidence files
- Image captions and EXIF metadata
- Re-analyze individual images
- Latest analysis results

#### 🎯 Suspects
- List of suspects with profiles
- Latest correlation results
- Interactive score visualizations
- Historical analysis records

#### 🤖 Ask Agent
- Text input for questions
- Configurable document retrieval count
- Markdown-formatted responses
- Citation tracking
- Conversation history (last 5 queries)

---

## 🔧 Configuration

### Environment Variables

See `env.example` for all options. Key UI-related settings:

```bash
# Maximum upload size (MB)
MAX_UPLOAD_SIZE_MB=100

# Streamlit port
STREAMLIT_PORT=8501

# Minimum confidence for suspect ranking
MIN_CONFIDENCE_THRESHOLD=0.65

# Enable/disable ethical guardrails
ENABLE_ETHICAL_GUARDRAILS=true
```

### Streamlit Configuration

Create `.streamlit/config.toml` for advanced settings:

```toml
[server]
port = 8501
maxUploadSize = 100

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[browser]
gatherUsageStats = false
```

---

## 🎯 User Workflows

### Workflow 1: Upload and Analyze Evidence

1. Select a case from the sidebar
2. Click "Choose an image" in the Upload Evidence section
3. Select an image file
4. Click "🔍 Upload & Analyze"
5. View the caption and EXIF metadata in the main area
6. (Optional) Click "🔄 Rebuild" to update the RAG index

### Workflow 2: Rank Suspects

1. Ensure evidence is uploaded and indexed
2. Click "🎯 Correlate Evidence" in the sidebar
3. View the results:
   - Bar chart of suspect scores
   - Detailed rankings with matched clues
   - Contributing evidence documents

### Workflow 3: Ask Questions

1. Navigate to the "🤖 Ask Agent" tab
2. Type a question (e.g., "What evidence points to John?")
3. (Optional) Adjust the number of documents to retrieve
4. Click "🚀 Ask Agent"
5. Read the answer with citations
6. View previous queries in the conversation history

---

## 📊 Display Components

### Image Analysis Display

When an image is analyzed:
- **Caption**: AI-generated description
- **Image ID**: Database reference
- **EXIF Metadata** (if available):
  - 📅 Date/Time
  - 📍 GPS coordinates
  - 📷 Camera model
  - 🔧 Raw EXIF fields

### Correlation Results Display

Interactive visualization with:
- **Bar Chart**: Color-coded suspect scores (0-1 scale)
- **Detailed Table**:
  - Rank and score
  - Vector similarity component
  - Keyword score component
  - Matched clues list
  - Top 3 contributing documents

### Agent Response Display

Markdown-formatted answer with:
- **Answer Text**: Full response with formatting
- **Citations**: Expandable list of source documents
- **Ranked Results**: Embedded correlation chart (if ranking query)
- **Query Details**: Metadata about the query (expandable)

---

## 🔒 Security Features

### In the UI

1. **File Encryption**: All uploads encrypted before storage
2. **In-Memory Processing**: Decrypted data never written to disk
3. **Configuration Validation**: Startup checks for required secrets
4. **Error Handling**: Graceful failures with user-friendly messages

### User Notifications

- ✅ Success toasts for completed actions
- ⚠️ Warnings for validation issues
- ❌ Errors with actionable messages
- 🔄 Spinners for long-running operations

---

## 🐛 Debugging

### Enable Debug Logging

The UI logs all actions to the console:

```bash
# View logs while running
streamlit run app/ui/app.py --logger.level=debug
```

### Common Issues

#### 1. **"Module not found" errors**

```bash
# Ensure venv is activated and dependencies installed
pip install -r requirements.txt
```

#### 2. **"Database connection failed"**

- Check PostgreSQL is running
- Verify `DATABASE_URL` in `.env`
- Run `python -m app.db.init_db` to initialize schema

#### 3. **"Configuration errors"**

- Ensure `.env` file exists
- Check all required variables are set:
  - `GEMINI_API_KEY`
  - `AES_MASTER_KEY` (64 hex characters)
  - `DATABASE_URL`

#### 4. **"Port already in use"**

```bash
# Use a different port
streamlit run app/ui/app.py --server.port=8502
```

#### 5. **Image upload fails**

- Check file size < `MAX_UPLOAD_SIZE_MB`
- Verify `FILES_DIR` is writable
- Check disk space

---

## 🧪 Manual QA Checklist

Before deploying, test the following:

### Upload & Analysis
- [ ] Upload a JPG image → caption displayed
- [ ] Upload a PNG image → EXIF shown (if available)
- [ ] Upload oversized file → error message shown
- [ ] Upload with no EXIF → generic caption generated

### RAG Index
- [ ] Click "Rebuild" → success toast appears
- [ ] Document count updates after rebuild
- [ ] Index persists across restarts

### Correlation
- [ ] Click "Correlate Evidence" → bar chart appears
- [ ] Suspect scores in [0, 1] range
- [ ] Clues and documents listed
- [ ] Empty case → "insufficient evidence" message

### Agent Q&A
- [ ] Ask ranking question → suspects ranked
- [ ] Ask general question → answer with citations
- [ ] Empty query → validation message
- [ ] Long query → truncated context, no crash

### Edge Cases
- [ ] No cases → prompt to create one
- [ ] No suspects → info message
- [ ] No evidence → info message
- [ ] Database offline → error message (not crash)

---

## 📈 Performance Tips

### For Large Cases

1. **Limit retrieval**: Use lower `k` values (3-6 docs)
2. **Batch operations**: Upload multiple images, then rebuild index once
3. **Cache results**: Correlation results saved to DB for replay

### For Slow Queries

1. Check RAG index is built (`Rebuild` button)
2. Reduce number of documents retrieved
3. Verify Gemini API key is valid (rate limits)

---

## 🎨 Customization

### Add Custom Tabs

Edit `app/ui/app.py`:

```python
def render_main_content(case_id: Optional[int]):
    # ...
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🔍 Evidence",
        "🎯 Suspects",
        "🤖 Ask Agent",
        "🆕 Custom Tab"  # Your new tab
    ])
    
    # ...
    
    with tab5:
        render_custom_tab(case_id)


def render_custom_tab(case_id: int):
    st.subheader("🆕 Custom Feature")
    # Your custom UI here
```

### Change Theme Colors

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#YOUR_COLOR"
```

### Add New Sidebar Actions

Edit the `render_sidebar()` function:

```python
def render_sidebar():
    # ...
    st.sidebar.header("🆕 Custom Action")
    
    if st.sidebar.button("Custom Button"):
        # Your action here
        pass
```

---

## 📚 Code Structure

```
app/ui/
├── __init__.py         # Module initialization
├── app.py              # Main Streamlit application
└── README.md           # This file
```

### Key Functions in `app.py`

| Function | Purpose |
|----------|---------|
| `main()` | Application entry point, orchestrates UI |
| `init_session_state()` | Initialize Streamlit session variables |
| `validate_configuration()` | Check required environment variables |
| `render_sidebar()` | Render sidebar with case selection and actions |
| `render_main_content()` | Render main content area with tabs |
| `render_overview_tab()` | Display case statistics and activity |
| `render_evidence_tab()` | Display uploaded evidence files |
| `render_suspects_tab()` | Display suspects and correlation results |
| `render_agent_tab()` | Display AI agent Q&A interface |
| `upload_and_analyze_image()` | Handle image upload, encryption, analysis |
| `rebuild_case_index()` | Rebuild RAG vector index |
| `run_correlation()` | Execute evidence correlation |
| `display_image_analysis()` | Format and display image analysis results |
| `display_correlation_results()` | Format and display correlation charts |
| `display_agent_response()` | Format and display agent Q&A results |

---

## 🔗 Integration Points

### With Backend Modules

```python
# Database operations
from app.db import get_all_cases, add_case, add_image, get_suspects_by_case

# Custom tools
from app.tools import analyze_image, correlate_and_persist

# RAG system
from app.rag import build_case_index, get_case_index_status

# AI agent
from app.agent import answer_question, to_markdown

# Security
from app.security import get_crypto_service
```

### Session State Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `selected_case_id` | `int | None` | Currently selected case |
| `last_analysis_result` | `dict | None` | Most recent image analysis |
| `last_correlation_result` | `dict | None` | Most recent correlation |
| `conversation_history` | `list[dict]` | Agent Q&A history |

---

## 📄 Example Usage

### Run Development Server

```bash
# Standard
streamlit run app/ui/app.py

# With custom port
streamlit run app/ui/app.py --server.port=8502

# With debug logging
streamlit run app/ui/app.py --logger.level=debug
```

### Run in Production

```bash
# With headless mode
streamlit run app/ui/app.py \
  --server.headless=true \
  --server.port=8501 \
  --server.address=0.0.0.0
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app/ui/app.py", "--server.headless=true"]
```

---

## 🆘 Support

### Logs Location

- **Console**: Real-time logs in terminal
- **Streamlit Logs**: `~/.streamlit/logs/`
- **Application Logs**: See `config.py` for `LOG_LEVEL`

### Error Messages

All errors are logged with context:
- User action that triggered the error
- Affected case/evidence ID
- Full stack trace (in console)

### Getting Help

1. Check console logs for detailed errors
2. Verify all environment variables are set
3. Test database connection: `python -m app.db.init_db`
4. Validate configuration: `python config.py`

---

**Built with ❤️ using Streamlit, LangChain, and Gemini Pro**

