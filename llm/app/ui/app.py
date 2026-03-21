"""
Streamlit UI for Forensic Crime Analysis Agent

A comprehensive dashboard for forensic case management, evidence analysis,
and AI-powered suspect ranking with transparent reasoning.

Features:
- Case management and selection
- Evidence upload with automatic encryption and analysis
- RAG-based semantic search and indexing
- Evidence correlation and suspect ranking
- AI-powered Q&A with guardrails

Run with:
    streamlit run app/ui/app.py
"""

import streamlit as st
import logging
import json
import os
import sys
import base64
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
import plotly.graph_objects as go
from plotly.subplots import make_subplots


project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


try:
    from config import config, Config
    from app.db import (
        get_all_cases,
        get_case,
        add_case,
        add_image,
        get_suspects_by_case,
        get_images_by_case,
        get_analysis_results,
        get_case_data,
        init_db,
        delete_text_document,
        delete_image
    )
    from app.tools import (
        analyze_image,
        batch_analyze_images,
        correlate_and_persist,
        ImageAnalysisError
    )
    from app.rag import build_case_index, get_case_index_status
    from app.agent import answer_question, to_markdown
    from app.security import get_crypto_service
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.info("Make sure you're running from the project root: `streamlit run app/ui/app.py`")
    st.stop()






st.set_page_config(
    page_title="Forensic Crime Analysis Dashboard",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)






def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'selected_case_id' not in st.session_state:
        st.session_state.selected_case_id = None
    
    if 'last_analysis_result' not in st.session_state:
        st.session_state.last_analysis_result = None
    
    if 'last_correlation_result' not in st.session_state:
        st.session_state.last_correlation_result = None
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'suspect_form_key' not in st.session_state:
        st.session_state.suspect_form_key = 0
    
    if 'text_form_key' not in st.session_state:
        st.session_state.text_form_key = 0
    
    if 'success_messages' not in st.session_state:
        st.session_state.success_messages = []
    


    if 'user_id' not in st.session_state:
        user_id_file = Path.home() / '.forensic_agent_user_id'
        try:

            if user_id_file.exists():
                with open(user_id_file, 'r') as f:
                    user_id = f.read().strip()
                    if user_id:
                        st.session_state.user_id = user_id
                        logger.info(f"✅ Loaded persistent user_id: {user_id}")
                    else:
                        raise FileNotFoundError
            else:
                raise FileNotFoundError
        except (FileNotFoundError, IOError):

            import uuid
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            st.session_state.user_id = user_id
            try:
                with open(user_id_file, 'w') as f:
                    f.write(user_id)
                logger.info(f"✅ Generated and saved new user_id: {user_id}")
            except IOError as e:
                logger.warning(f"⚠️ Could not save user_id to file: {e}. Using session-only user_id.")






def get_type_badge_color(source_type: str) -> str:
    """Get color for evidence type badge"""
    color_map = {
        "witness_statement": "#4ECDC4",
        "forensic_report": "#FF6B6B",
        "cctv_video": "#95E1D3",
        "timeline": "#F38181",
        "digital_evidence": "#AA96DA",
        "scene_notes": "#FCBAD3",
        "physical_object": "#FFD93D",
        "autopsy_report": "#6BCF7F",
        "alibi": "#FFA07A",
        "other": "#B0B0B0"
    }
    return color_map.get(source_type, "#B0B0B0")


def get_type_icon(source_type: str) -> str:
    """Get icon for evidence type"""
    icon_map = {
        "witness_statement": "👤",
        "forensic_report": "🧪",
        "cctv_video": "🎥",
        "timeline": "⏰",
        "digital_evidence": "💻",
        "scene_notes": "📝",
        "physical_object": "🔍",
        "autopsy_report": "⚕️",
        "alibi": "🛡️",
        "other": "📄"
    }
    return icon_map.get(source_type, "📄")


def render_evidence_card(text_doc, is_dark: bool = False):
    """Render a modern evidence preview card"""
    bg_color = "#1E1E1E" if is_dark else "#FFFFFF"
    text_color = "#FFFFFF" if is_dark else "#000000"
    border_color = "#444444" if is_dark else "#E0E0E0"
    badge_color = get_type_badge_color(text_doc.source_type)
    icon = get_type_icon(text_doc.source_type)
    preview = text_doc.content[:150] + "..." if len(text_doc.content) > 150 else text_doc.content
    
    card_html = f"""
    <div style="
        background-color: {bg_color};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <div style="flex: 1;">
                <h4 style="margin: 0; color: {text_color}; font-size: 16px;">
                    {icon} {text_doc.title}
                </h4>
            </div>
            <span style="
                background-color: {badge_color};
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
            ">{text_doc.source_type.replace('_', ' ')}</span>
        </div>
        <p style="
            color: {text_color if not is_dark else '#CCCCCC'};
            font-size: 13px;
            margin: 8px 0;
            line-height: 1.5;
        ">{preview}</p>
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid {border_color};
        ">
            <span style="color: {text_color if not is_dark else '#AAAAAA'}; font-size: 11px;">
                📄 ID: {text_doc.id} • Added: {text_doc.created_at.strftime('%Y-%m-%d %H:%M')}
            </span>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_image_card(image, is_dark: bool = False):
    """Render a modern image evidence preview card"""
    bg_color = "#1E1E1E" if is_dark else "#FFFFFF"
    text_color = "#FFFFFF" if is_dark else "#000000"
    border_color = "#444444" if is_dark else "#E0E0E0"
    preview = image.caption_text[:150] + "..." if image.caption_text and len(image.caption_text) > 150 else (image.caption_text or "No analysis yet")
    
    card_html = f"""
    <div style="
        background-color: {bg_color};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <div style="flex: 1;">
                <h4 style="margin: 0; color: {text_color}; font-size: 16px;">
                    🖼️ {image.filename}
                </h4>
            </div>
            <span style="
                background-color: #95E1D3;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
            ">IMAGE</span>
        </div>
        <p style="
            color: {text_color if not is_dark else '#CCCCCC'};
            font-size: 13px;
            margin: 8px 0;
            line-height: 1.5;
        ">{preview}</p>
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid {border_color};
        ">
            <span style="color: {text_color if not is_dark else '#AAAAAA'}; font-size: 11px;">
                🖼️ ID: {image.id} • Uploaded: {image.created_at.strftime('%Y-%m-%d %H:%M')}
            </span>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def parse_score_components(reasoning_trace: List[str]) -> Dict[str, float]:
    """Parse score components from reasoning trace"""
    components = {
        "Decisive Evidence": 0.0,
        "Timeline": 0.0,
        "Vector Similarity": 0.0,
        "Contradictions": 0.0,
        "Name/Keyword Score": 0.0
    }
    
    for line in reasoning_trace:
        line_lower = line.lower()

        try:
            if line.startswith("+") or line.startswith("-"):
                value_str = line.split()[0]
                value = float(value_str)
            else:

                match = re.search(r'([+-]?\d+\.?\d*)', line)
                if match:
                    value = float(match.group(1))
                else:
                    continue
        except (ValueError, IndexError):
            continue
        

        if any(term in line_lower for term in ["decisive", "fingerprint", "dna", "cctv", "weapon", "prints"]):
            components["Decisive Evidence"] += value
        elif any(term in line_lower for term in ["timeline", "murder window", "proximity"]):
            components["Timeline"] += value
        elif any(term in line_lower for term in ["similarity", "semantic", "vector"]):
            components["Vector Similarity"] += value
        elif any(term in line_lower for term in ["contradiction", "penalty"]):
            components["Contradictions"] += value
        elif any(term in line_lower for term in ["name", "keyword", "mention"]):
            components["Name/Keyword Score"] += value
    
    return components






def validate_configuration() -> bool:
    """
    Validate application configuration
    
    Returns:
        True if configuration is valid, False otherwise
    """
    errors = Config.validate()
    
    if errors:
        st.sidebar.error("⚠️ Configuration Issues")
        for error in errors:
            st.sidebar.warning(f"• {error}")
        
        with st.sidebar.expander("📋 Setup Instructions", expanded=True):
            st.markdown("""
            **To fix configuration:**
            
            1. Create a `.env` file in the project root
            2. Add required variables:
            ```bash
            GEMINI_API_KEY=your_api_key_here
            DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/forensic_db
            AES_MASTER_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
            ```
            3. Restart the application
            
            See `env.example` for a complete template.
            """)
        
        return False
    
    return True






def get_cases_list() -> List[Dict[str, Any]]:
    """
    Retrieve all cases from database
    
    Returns:
        List of case dictionaries with id, title, description
    """
    try:
        with st.spinner("Loading cases..."):
            cases = get_all_cases()
            logger.info(f"Retrieved {len(cases)} cases from database")
            return cases
    except Exception as e:
        logger.error(f"Error loading cases: {e}")
        st.error(f"❌ Error loading cases: {e}")
        return []


def create_new_case(title: str, description: str) -> Optional[int]:
    """
    Create a new case in the database
    
    Args:
        title: Case title
        description: Case description
    
    Returns:
        Case ID if successful, None otherwise
    """
    try:
        with st.spinner("Creating case..."):
            case = add_case(title=title, description=description)
            if case:
                logger.info(f"Created case {case.id}: {title}")
                st.success(f"✅ Case created successfully! (ID: {case.id})")
                st.toast(f"✅ Case #{case.id} created", icon="✅")
                return case.id
            else:
                st.error("Failed to create case")
                return None
    except Exception as e:
        logger.error(f"Error creating case: {e}")
        st.error(f"❌ Error creating case: {e}")
        return None




















def upload_and_analyze_image(
    uploaded_file,
    case_id: int,
    description: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Upload, encrypt, and analyze an image file
    
    SECURITY: This function ensures all uploaded files are encrypted before storage.
    
    Process:
    1. Validate file size
    2. Read file bytes into memory
    3. **Encrypt using AES-256-CBC** (CryptoService)
    4. Save encrypted file to disk
    5. Store encryption metadata (IV, HMAC) in database
    6. Analyze image in-memory (EXIF + caption)
    7. Clear plaintext from memory
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        case_id: ID of the case to associate the image with
        description: Optional description of the image
    
    Returns:
        Analysis result dictionary if successful, None otherwise
    """
    try:

        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > config.MAX_UPLOAD_SIZE_MB:
            st.error(f"❌ File size ({file_size_mb:.1f} MB) exceeds limit ({config.MAX_UPLOAD_SIZE_MB} MB)")
            return None
        
        logger.info(f"Uploading image: {uploaded_file.name} ({file_size_mb:.2f} MB)")
        

        file_bytes = uploaded_file.getvalue()
        

        crypto_service = get_crypto_service()
        
        with st.spinner("🔐 Encrypting file..."):
            encryption_result = crypto_service.encrypt_file(
                filename=uploaded_file.name,
                data=file_bytes,
                output_dir=str(config.FILES_DIR)
            )
        
        logger.info(f"File encrypted: {encryption_result['file_path']}")
        

        iv_hex = base64.b64decode(encryption_result['iv_base64']).hex()
        hmac_hex = base64.b64decode(encryption_result['hmac_base64']).hex()
        

        with st.spinner("💾 Saving to database..."):
            image = add_image(
                case_id=case_id,
                filename=uploaded_file.name,
                file_path=encryption_result['file_path'],
                iv_hex=iv_hex,
                sha256_hex=hmac_hex
            )
        
        if not image:
            st.error("Failed to save image to database")
            return None
        
        logger.info(f"Image saved to database: ID {image.id}")
        

        with st.spinner("🔍 Analyzing image (EXIF + caption)..."):
            analysis_result = analyze_image(image.id)
        
        logger.info(f"Image analysis complete: {analysis_result['caption'][:100]}...")
        
        return analysis_result
        
    except ImageAnalysisError as e:
        logger.error(f"Image analysis error: {e}")
        st.error(f"❌ Image analysis failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error uploading image: {e}", exc_info=True)
        st.error(f"❌ Error uploading image: {e}")
        return None


def rebuild_case_index(case_id: int) -> bool:
    """
    Rebuild RAG index for a case with LLM-based relevance filtering at ingestion.
    
    Args:
        case_id: Case ID to rebuild index for
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with st.spinner("🔄 Rebuilding vector index with LLM filtering..."):
            logger.info(f"Rebuilding index for case {case_id}")
            result = build_case_index(case_id, force_rebuild=True)
            

            if result.get('llm_filter_failed'):
                st.warning(
                    f"⚠️ **LLM Filtering Unavailable During Indexing**: "
                    f"Evidence relevance filtering failed ({result.get('llm_filter_failure_count', 0)} failure(s)). "
                    f"Some irrelevant documents may have been indexed. "
                    f"LLM may be down or API key missing."
                )
                st.toast("⚠️ LLM filtering unavailable during indexing", icon="⚠️")
            

            status = get_case_index_status(case_id)
            
            logger.info(f"Index rebuilt: {status}")
            doc_count = status.get('document_count', 0)
            source_breakdown = status.get('source_breakdown', {})
            

            from app.db import get_texts_by_case, get_images_by_case, get_suspects_by_case
            total_texts = len(get_texts_by_case(case_id))
            total_images = len([img for img in get_images_by_case(case_id) if img.caption_text])
            total_suspects = len(get_suspects_by_case(case_id))
            

            indexed_texts = sum(
                count for source_type, count in source_breakdown.items() 
                if source_type not in ['image', 'suspect']
            )
            indexed_images = source_breakdown.get('image', 0)
            indexed_suspects = source_breakdown.get('suspect', 0)
            
            filtered_texts = total_texts - indexed_texts
            filtered_images = total_images - indexed_images
            filtered_suspects = total_suspects - indexed_suspects
            

            st.success(f"✅ Index rebuilt: {doc_count} documents indexed")
            

            st.markdown("### 📊 Indexing Details")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Text Evidence", f"{indexed_texts}/{total_texts}")
            with col2:
                st.metric("Images", f"{indexed_images}/{total_images}")
            with col3:
                st.metric("Suspects", f"{indexed_suspects}/{total_suspects}")
            

            if filtered_texts > 0 or filtered_images > 0:
                st.info(
                    f"ℹ️ **LLM Relevance Filter**: {filtered_texts + filtered_images} document(s) were filtered out "
                    f"because they don't contain crime-relevant information (no specific people/actions/timeline connections). "
                    f"This keeps the search index focused on useful evidence."
                )
                if filtered_images > 0:
                    st.warning(f"⚠️ {filtered_images} image(s) filtered - images with no forensic evidence or crime context are excluded.")
                if filtered_texts > 0:
                    st.warning(f"⚠️ {filtered_texts} text document(s) filtered - documents without crime-relevant details are excluded.")
            else:
                st.success("✅ All documents passed the relevance filter and were indexed.")
            
            st.toast(f"✅ Index rebuilt ({doc_count} docs)", icon="🔄")
            
            return True
            
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}", exc_info=True)
        st.error(f"❌ Error rebuilding index: {e}")
        return False


def run_correlation(case_id: int, query: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Run evidence correlation to rank suspects
    
    Args:
        case_id: Case ID to correlate evidence for
        query: Optional custom query for evidence extraction
    
    Returns:
        Correlation result dictionary if successful, None otherwise
    """
    try:
        with st.spinner("🔍 Correlating evidence with suspects..."):
            logger.info(f"Running correlation for case {case_id}")
            
            result = correlate_and_persist(case_id, query=query, k=8)
            
            if 'error' in result:
                st.warning(f"⚠️ {result.get('message', 'Insufficient evidence')}")
                logger.warning(f"Correlation returned error: {result}")
                return None
            
            logger.info(f"Correlation complete: {len(result['ranked'])} suspects ranked")
            st.success(f"✅ Correlation complete: {len(result['ranked'])} suspects ranked")
            st.toast("✅ Suspects ranked", icon="🎯")
            
            return result
            
    except Exception as e:
        logger.error(f"Error running correlation: {e}", exc_info=True)
        st.error(f"❌ Error running correlation: {e}")
        return None






def display_image_analysis(result: Dict[str, Any]):
    """
    Display image analysis results
    
    Args:
        result: Analysis result from analyze_image()
    """
    st.subheader("📸 Image Analysis Results")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Caption:**")
        st.info(result.get('caption', 'No caption generated'))
    
    with col2:
        st.metric("Image ID", result.get('image_id', 'N/A'))
    

    exif = result.get('exif', {})
    if exif and exif != {}:
        with st.expander("🔍 EXIF Metadata", expanded=True):

            exif_display = {}
            
            if 'datetime' in exif and exif['datetime']:
                exif_display['📅 Date/Time'] = exif['datetime']
            
            if 'gps' in exif and exif['gps']:
                gps = exif['gps']
                exif_display['📍 GPS'] = f"{gps.get('lat', 'N/A')}, {gps.get('lon', 'N/A')}"
            
            if 'camera' in exif and exif['camera']:
                exif_display['📷 Camera'] = exif['camera']
            
            if 'raw' in exif and exif['raw']:
                exif_display['🔧 Raw Data'] = f"{len(exif['raw'])} fields"
            
            if exif_display:
                for label, value in exif_display.items():
                    st.text(f"{label}: {value}")
            else:
                st.text("No EXIF metadata extracted")
    else:
        st.info("ℹ️ No EXIF metadata available")


def generate_ranking_pdf(result: Dict[str, Any]) -> bytes:
    """
    Generate a PDF report of suspect correlation rankings
    
    Args:
        result: Correlation result from correlate_and_persist()
        
    Returns:
        PDF file as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=1
    )
    story.append(Paragraph("Forensic Crime Analysis Report", title_style))
    story.append(Paragraph("Suspect Correlation Rankings", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    

    case_id = result.get('case_id', 'N/A')
    query = result.get('query', 'Default evidence query')
    docs_used = result.get('docs_used', 0)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    metadata_text = f"""
    <b>Case ID:</b> {case_id}<br/>
    <b>Analysis Query:</b> {query}<br/>
    <b>Evidence Documents Analyzed:</b> {docs_used}<br/>
    <b>Report Generated:</b> {timestamp}
    """
    story.append(Paragraph(metadata_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    ranked = result.get('ranked', [])
    
    if not ranked:
        story.append(Paragraph("No suspects found or all scores are zero.", styles['Normal']))
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    

    story.append(Paragraph("Ranking Summary", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    

    summary_data = [['Rank', 'Suspect Name', 'Score', 'Vector Sim', 'Keyword Score', 'Decisive Evidence']]
    for idx, r in enumerate(ranked, 1):

        decisive_score = 0.0
        if 'reasoning_trace' in r and r['reasoning_trace']:
            parsed_components = parse_score_components(r['reasoning_trace'])
            decisive_score = parsed_components.get("Decisive Evidence", 0.0)
        
        summary_data.append([
            str(idx),
            r['suspect_name'],
            f"{r['score']:.3f}",
            f"{r['components'].get('base_sim', 0):.3f}",
            f"{r['components'].get('keyword_score', 0):.3f}",
            f"{decisive_score:+.3f}"
        ])
    
    summary_table = Table(summary_data, colWidths=[0.5*inch, 2*inch, 0.8*inch, 1*inch, 1*inch, 1.2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    

    story.append(Paragraph("Detailed Analysis", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    for idx, r in enumerate(ranked, 1):

        suspect_header = f"#{idx} - {r['suspect_name']} (Score: {r['score']:.3f})"
        story.append(Paragraph(suspect_header, styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        

        components_dict = {
            "Vector Similarity": r['components'].get('base_sim', 0),
            "Name/Keyword Score": r['components'].get('keyword_score', 0),
        }
        

        if 'reasoning_trace' in r and r['reasoning_trace']:
            parsed_components = parse_score_components(r['reasoning_trace'])
            components_dict.update(parsed_components)
        
        components_text = "<b>Score Components:</b><br/>"
        for comp_name, comp_value in components_dict.items():
            if abs(comp_value) > 0.001:
                sign = "+" if comp_value >= 0 else ""
                components_text += f"• {comp_name}: {sign}{comp_value:.3f}<br/>"
        
        story.append(Paragraph(components_text, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        

        if 'reasoning_trace' in r and r['reasoning_trace']:
            reasoning_text = "<b>🧠 Reasoning Trace (How Score Was Calculated):</b><br/>"
            for line in r['reasoning_trace']:

                clean_line = line.replace("+", "+").replace("-", "-")
                reasoning_text += f"• {clean_line}<br/>"
            story.append(Paragraph(reasoning_text, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        

        if r['matched_clues']:
            clues_text = "<b>Matched Clues:</b><br/>" + "<br/>".join([f"• {clue}" for clue in r['matched_clues']])
            story.append(Paragraph(clues_text, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        

        if 'contributing_docs' in r and r['contributing_docs']:
            docs_text = "<b>Top Contributing Evidence:</b><br/>"
            for doc_item in r['contributing_docs'][:3]:
                doc_title = doc_item.get('title', 'Untitled')
                doc_score = doc_item.get('score', 0)
                docs_text += f"• {doc_title} (relevance: {doc_score:.3f})<br/>"
            story.append(Paragraph(docs_text, styles['Normal']))
        
        story.append(Spacer(1, 0.2*inch))
        

        if idx < len(ranked):
            story.append(PageBreak())
    

    story.append(Spacer(1, 0.3*inch))
    footer_text = """
    <i><b>Important Note:</b> This analysis is decision support only, not a legal conclusion. 
    The rankings are based on correlation between suspect profiles and available evidence. 
    They do not constitute proof of guilt and should be used to guide further investigation, 
    not as definitive findings. All suspects are presumed innocent.</i>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _render_suspect_details(r: Dict[str, Any]):
    """Helper function to render suspect details (used to avoid nested expanders)"""

    if 'reasoning_trace' in r and r['reasoning_trace']:
        components = parse_score_components(r['reasoning_trace'])
        

        components["Vector Similarity"] = r['components'].get('base_sim', 0)
        components["Name/Keyword Score"] = r['components'].get('keyword_score', 0)
        

        fig = go.Figure()
        
        component_names = list(components.keys())
        component_values = list(components.values())
        colors_bar = ['#6BCF7F' if v >= 0 else '#FF6B6B' for v in component_values]
        
        fig.add_trace(go.Bar(
            x=component_values,
            y=component_names,
            orientation='h',
            marker=dict(color=colors_bar),
            text=[f"{v:+.3f}" for v in component_values],
            textposition='outside'
        ))
        
        fig.update_layout(
            title=f"Score Breakdown: {r['suspect_name']}",
            xaxis_title="Score Contribution",
            yaxis_title="Component",
            height=300,
            template="plotly_white",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Components:**")
        st.text(f"• Vector Similarity: {r['components'].get('base_sim', 0):.3f}")
        st.text(f"• Keyword Score: {r['components'].get('keyword_score', 0):.3f}")
    
    with col2:
        st.markdown("**Matched Clues:**")
        if r['matched_clues']:
            for clue in r['matched_clues']:
                st.text(f"• {clue}")
        else:
            st.text("• No specific clues")
    

    if 'reasoning_trace' in r and r['reasoning_trace']:
        st.markdown("---")
        st.markdown("**🧠 Reasoning Trace (How Score Was Calculated):**")
        for line in r['reasoning_trace']:
            st.write("• " + line)
    

    if 'contributing_docs' in r and r['contributing_docs']:
        st.markdown("**Top Contributing Evidence:**")
        for doc in r['contributing_docs'][:3]:
            doc_title = doc.get('title', 'Untitled')
            doc_score = doc.get('score', 0)
            st.text(f"• {doc_title} (relevance: {doc_score:.3f})")


def display_correlation_results(result: Dict[str, Any], use_expanders: bool = True):
    """
    Display evidence correlation results with bar chart, timeline visualization, and scoring breakdown
    
    Args:
        result: Correlation result from correlate_and_persist()
        use_expanders: Whether to use expanders for suspect details (default: True)
                      Set to False when called from within another expander
    """
    st.subheader("🎯 Suspect Correlation Results")
    
    ranked = result.get('ranked', [])
    case_id = result.get('case_id')
    
    if not ranked:
        st.warning("No suspects found or all scores are zero")
        return
    

    df = pd.DataFrame([
        {
            'Suspect': r['suspect_name'],
            'Score': r['score'],
            'Base Similarity': r['components'].get('base_sim', 0),
            'Keyword Score': r['components'].get('keyword_score', 0),
            'Matched Clues': ', '.join(r['matched_clues'][:3]) if r['matched_clues'] else 'None'
        }
        for r in ranked
    ])
    

    df = df.sort_values('Score', ascending=False).reset_index(drop=True)
    

    st.markdown("**Suspect Correlation Scores:**")
    

    chart_data = df.set_index('Suspect')['Score'].to_dict()
    

    for suspect_name, score in chart_data.items():
        width_pct = min(int(score * 100), 100)
        st.markdown(
            f"""
            <div style="margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <strong>{suspect_name}</strong>
                    <span style="font-weight: bold; color: #4ECDC4;">{score:.3f}</span>
                </div>
                <div style="background: #e0e0e0; height: 25px; border-radius: 5px; position: relative; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #4ECDC4, #6BCF7F); width: {width_pct}%; height: 100%; transition: width 0.3s;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    

    st.markdown("---")
    st.markdown("**Detailed Rankings:**")
    
    for idx, r in enumerate(ranked, 1):

        if use_expanders:
            with st.expander(f"#{idx} - {r['suspect_name']} (Score: {r['score']:.3f})", expanded=(idx == 1)):
                _render_suspect_details(r)
        else:
            st.markdown(f"### #{idx} - {r['suspect_name']} (Score: {r['score']:.3f})")
            _render_suspect_details(r)
    

    st.markdown("---")
    pdf_bytes = generate_ranking_pdf(result)
    st.download_button(
        label="📄 Export Ranking as PDF",
        data=pdf_bytes,
        file_name=f"forensic_ranking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )


def display_agent_response(result: Dict[str, Any]):
    """
    Display agent Q&A response
    
    Args:
        result: Response from answer_question()
    """
    st.subheader("🤖 Agent Response")
    


    tool_results = result.get('tool_results', [])
    tools_used = result.get('tools_used', [])
    

    if tool_results and 'get_case_summary' not in tools_used:
        with st.expander("🔧 Tool Outputs", expanded=True):
            for tool_result in tool_results:
                st.markdown(f"**Tool: {tool_result['tool']}**")

                st.code(tool_result['print_block'], language='text')
                st.markdown("---")
    

    answer = result.get('answer', 'No response generated')
    st.markdown(answer)
    

    tools_used = result.get('tools_used', [])
    if tools_used:
        st.markdown("---")
        st.markdown("### 🔧 Tools Used")
        for tool_name in tools_used:

            tool_key = f"tool_code_{tool_name}"
            with st.expander(f"📋 {tool_name}", expanded=False):
                try:
                    from app.agent.forensic_agent import get_tool_code
                    tool_code = get_tool_code(tool_name)
                    st.code(tool_code, language='python')
                except Exception as e:
                    st.error(f"Error loading tool code: {e}")
    


    if 'ranked' in result and result['ranked']:
        st.markdown("---")
        with st.expander("📊 Detailed Correlation Analysis", expanded=False):

            display_correlation_results(result, use_expanders=False)
    

    if 'components' in result:
        with st.expander("🔍 Query Details", expanded=False):
            st.json(result['components'])






def render_sidebar():
    """Render sidebar with case selection and actions"""
    st.sidebar.title("🕵️ Dashboard")
    

    st.sidebar.header("📁 Case Selection")
    
    cases = get_cases_list()
    
    if not cases:
        st.sidebar.warning("No cases found")
        

        with st.sidebar.expander("➕ Create New Case", expanded=True):
            with st.form("create_case_form"):
                new_title = st.text_input("Case Title", placeholder="Murder at Oak Street")
                new_description = st.text_area("Description", placeholder="Details about the case...")
                
                if st.form_submit_button("Create Case", use_container_width=True):
                    if new_title and new_description:
                        case_id = create_new_case(new_title, new_description)
                        if case_id:
                            st.session_state.selected_case_id = case_id
                            st.rerun()
                    else:
                        st.warning("Please fill in all fields")
        
        return None
    

    case_options = {f"[{c.id}] {c.title}": c.id for c in cases}
    case_options = {"-- Select a case --": None, **case_options}
    

    try:
        if st.session_state.selected_case_id is None:
            default_index = 0
        elif st.session_state.selected_case_id in list(case_options.values()):
            default_index = list(case_options.values()).index(st.session_state.selected_case_id)
        else:
            default_index = 0
    except (ValueError, IndexError):
        default_index = 0
    
    selected_label = st.sidebar.selectbox(
        "Select Case",
        options=list(case_options.keys()),
        index=default_index
    )
    
    selected_case_id = case_options[selected_label]
    st.session_state.selected_case_id = selected_case_id
    

    with st.sidebar.expander("➕ Create New Case", expanded=False):
        with st.form("create_case_form_top"):
            new_title = st.text_input("Case Title", placeholder="Murder at Oak Street")
            new_description = st.text_area("Description", placeholder="Details about the case...")
            
            if st.form_submit_button("Create Case", use_container_width=True):
                if new_title and new_description:
                    case_id = create_new_case(new_title, new_description)
                    if case_id:
                        st.session_state.selected_case_id = case_id
                        st.rerun()
                else:
                    st.warning("Please fill in all fields")
    
    st.sidebar.markdown("---")
    
    if selected_case_id:

        case = get_case(selected_case_id)
        if case:
            with st.sidebar.expander("ℹ️ Case Info", expanded=False):
                st.text(f"ID: {case.id}")
                st.text(f"Title: {case.title}")
                st.text(f"Created: {case.created_at.strftime('%Y-%m-%d')}")
        

        st.sidebar.header("📤 Upload Evidence")
        
        with st.form("upload_form"):
            uploaded_file = st.file_uploader(
                "Choose an image",
                type=['jpg', 'jpeg', 'png', 'gif', 'bmp'],
                help="Upload evidence images for automatic analysis"
            )
            
            if st.form_submit_button("🔍 Upload & Analyze", use_container_width=True):
                if uploaded_file:
                    result = upload_and_analyze_image(uploaded_file, selected_case_id)
                    if result:
                        st.session_state.last_analysis_result = result
                        st.rerun()
                else:
                    st.warning("Please select a file first")
        

        st.sidebar.header("🔄 Evidence Index")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🔄 Rebuild", use_container_width=True, help="Rebuild RAG vector index"):
                rebuild_case_index(selected_case_id)
                st.rerun()
        
        with col2:

            try:
                status = get_case_index_status(selected_case_id)
                doc_count = status.get('document_count', 0)
                st.metric("Docs", doc_count)
            except Exception as e:
                logger.debug(f"Error getting index status: {e}")
                st.metric("Docs", "?")
        

        with st.sidebar.expander("📊 See Details", expanded=False):
            try:

                status = get_case_index_status(selected_case_id)
                source_breakdown = status.get('source_breakdown', {})
                

                from app.db import get_texts_by_case, get_images_by_case, get_suspects_by_case
                total_texts = len(get_texts_by_case(selected_case_id))
                total_images = len([img for img in get_images_by_case(selected_case_id) if img.caption_text])
                total_suspects = len(get_suspects_by_case(selected_case_id))
                

                indexed_texts = sum(
                    count for source_type, count in source_breakdown.items() 
                    if source_type not in ['image', 'suspect']
                )
                indexed_images = source_breakdown.get('image', 0)
                indexed_suspects = source_breakdown.get('suspect', 0)
                

                filtered_texts = total_texts - indexed_texts
                filtered_images = total_images - indexed_images
                filtered_suspects = total_suspects - indexed_suspects
                

                st.markdown("**Indexed Documents:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Texts", f"{indexed_texts}/{total_texts}")
                with col2:
                    st.metric("Images", f"{indexed_images}/{total_images}")
                with col3:
                    st.metric("Suspects", f"{indexed_suspects}/{total_suspects}")
                

                if filtered_texts > 0 or filtered_images > 0:
                    st.markdown("---")
                    st.markdown("**Filtered Out:**")
                    if filtered_texts > 0:
                        st.warning(f"📄 {filtered_texts} text document(s)")
                    if filtered_images > 0:
                        st.warning(f"🖼️ {filtered_images} image(s)")
                    
                    st.markdown("---")
                    st.info(
                        "**Why filtered?**\n\n"
                        "Documents are filtered if they don't contain:\n"
                        "• Specific people/vehicles/objects\n"
                        "• Actions, movements, or behaviors\n"
                        "• Time/timeline/location connections\n\n"
                        "This keeps the search index focused on crime-relevant evidence."
                    )
                else:
                    st.markdown("---")
                    st.success("✅ All documents indexed (none filtered)")
                    
            except Exception as e:
                logger.debug(f"Error showing index details: {e}")
                st.error("Could not load index details")
        

        st.sidebar.header("🎯 Analyze Suspects")
        
        if st.sidebar.button("🎯 Correlate Evidence", use_container_width=True):
            result = run_correlation(selected_case_id)
            if result:
                st.session_state.last_correlation_result = result
                st.rerun()
    
    return selected_case_id






def render_main_content(case_id: Optional[int]):
    """
    Render main content area
    
    Args:
        case_id: Selected case ID, or None if no case selected
    """
    st.title("🕵️ Forensic Crime Analysis Dashboard")
    
    if case_id is None:

        st.markdown("""
        ## Welcome to the Forensic Crime Analysis Agent
        
        This AI-powered system helps analyze crime scene evidence and rank suspects
        using advanced natural language processing and machine learning.
        
        ### 🚀 Getting Started
        
        1. **Select or create a case** in the sidebar
        2. **Upload evidence** (images with EXIF metadata)
        3. **Rebuild the index** to enable semantic search
        4. **Correlate evidence** to rank suspects
        5. **Ask questions** to the AI agent
        
        ### ✨ Features
        
        - 🔐 **Secure**: All files encrypted with AES-256-CBC
        - 🧠 **Intelligent**: Powered by Google Gemini Pro
        - 🔍 **Semantic Search**: RAG-based evidence retrieval
        - 📊 **Transparent**: Explainable suspect rankings
        - 🛡️ **Ethical**: Built-in guardrails and caveats
        
        ---
        
        👈 **Select a case from the sidebar to begin**
        """)
        

        col1, col2, col3 = st.columns(3)
        
        with col1:
            try:
                cases = get_all_cases()
                st.metric("📁 Total Cases", len(cases))
            except:
                st.metric("📁 Total Cases", "Error")
        
        with col2:
            api_key_status = "✅ Configured" if config.GEMINI_API_KEY else "❌ Missing"
            st.metric("🔑 API Key", api_key_status)
        
        with col3:
            db_status = "✅ Connected" if config.DATABASE_URL else "❌ Not Configured"
            st.metric("🗃️ Database", db_status)
        
        return
    

    case = get_case(case_id)
    
    if not case:
        st.error(f"❌ Case {case_id} not found")
        return
    

    st.header(f"📁 {case.title}")
    st.caption(case.description)
    

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "🔍 Evidence",
        "🎯 Suspects",
        "🤖 Ask Agent"
    ])
    

    with tab1:
        render_overview_tab(case_id)
    

    with tab2:
        render_evidence_tab(case_id)
    

    with tab3:
        render_suspects_tab(case_id)
    

    with tab4:
        render_agent_tab(case_id)


def render_overview_tab(case_id: int):
    """Render overview tab with case statistics"""
    st.subheader("📊 Case Overview")
    
    try:

        case_data = get_case_data(case_id)
        

        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            suspect_count = len(case_data.get('suspects', []))
            st.metric("👥 Suspects", suspect_count)
        
        with col2:
            text_count = len(case_data.get('text_documents', []))
            st.metric("📄 Documents", text_count)
        
        with col3:
            image_count = len(case_data.get('images', []))
            st.metric("📸 Images", image_count)
        
        with col4:


            analysis_results = case_data.get('analysis_results', [])
            if analysis_results:

                from collections import defaultdict
                runs_by_time = defaultdict(list)
                for result in analysis_results:
                    run_at = result.get('run_at', '')
                    runs_by_time[run_at].append(result)
                unique_runs = len(runs_by_time)

                latest_run = max(runs_by_time.keys()) if runs_by_time else None
                if latest_run:
                    from datetime import datetime
                    try:
                        latest_dt = datetime.fromisoformat(latest_run.replace('Z', '+00:00'))
                        latest_str = latest_dt.strftime('%Y-%m-%d %H:%M')
                        st.metric("🎯 Correlation Runs", unique_runs, help=f"Latest: {latest_str}")
                    except:
                        st.metric("🎯 Correlation Runs", unique_runs)
                else:
                    st.metric("🎯 Correlation Runs", unique_runs)
            else:
                st.metric("🎯 Correlation Runs", 0)
        

        st.markdown("### 📅 Recent Activity")
        
        activities = []
        

        for img in case_data.get('images', [])[:5]:
            activities.append({
                'time': img.get('created_at', 'Unknown'),
                'type': '📸 Image',
                'detail': img.get('filename', 'Unknown')
            })
        

        for txt in case_data.get('text_documents', [])[:5]:
            activities.append({
                'time': txt.get('created_at', 'Unknown'),
                'type': '📄 Document',
                'detail': txt.get('title', 'Unknown')
            })
        

        activities.sort(key=lambda x: x['time'], reverse=True)
        
        if activities:
            for act in activities[:10]:
                st.text(f"{act['time']} - {act['type']}: {act['detail']}")
        else:
            st.info("No activity yet. Upload evidence to get started!")
        
    except Exception as e:
        logger.error(f"Error rendering overview: {e}")
        st.error(f"Error loading case data: {e}")


def render_evidence_tab(case_id: int):
    """Render evidence tab with text documents and images"""
    st.subheader("🔍 Evidence Management")
    
    try:
        from app.db import add_text, get_texts_by_case
        

        texts = get_texts_by_case(case_id)
        images = get_images_by_case(case_id)
        

        if 'success_messages' in st.session_state and st.session_state.success_messages:
            for msg in st.session_state.success_messages:
                st.success(msg)

            st.session_state.success_messages = []
        

        with st.expander("➕ Add Text Evidence", expanded=(len(texts) == 0 and len(images) == 0)):
            with st.form(f"add_text_form_{st.session_state.text_form_key}"):
                st.markdown("**Add witness statements, forensic reports, or investigative notes**")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    text_title = st.text_input(
                        "Document Title*",
                        placeholder="Witness Statement - Sarah Wilson",
                        help="Descriptive title for this evidence"
                    )
                
                with col2:
                    source_type = st.selectbox(
                        "Source Type*",
                        options=[
                            "witness_statement",
                            "forensic_report",
                            "cctv_video",
                            "timeline",
                            "digital_evidence",
                            "scene_notes",
                            "physical_object",
                            "autopsy_report",
                            "alibi",
                            "other"
                        ],
                        help="Type of evidence document"
                    )
                
                text_content = st.text_area(
                    "Content*",
                    placeholder="Enter the full text of the document here...",
                    help="The actual content of the evidence document",
                    height=200
                )
                
                submitted = st.form_submit_button("➕ Add Text Evidence", use_container_width=True)
                
                if submitted:
                    if text_title and text_content:
                        try:
                            new_text = add_text(
                                case_id=case_id,
                                source_type=source_type,
                                title=text_title,
                                content=text_content
                            )
                            
                            if new_text:

                                if 'success_messages' not in st.session_state:
                                    st.session_state.success_messages = []
                                st.session_state.success_messages.append(
                                    f"✅ Text evidence '{text_title}' added successfully! (ID: {new_text.id})"
                                )
                                logger.info(f"Added text evidence: {text_title} to case {case_id}")

                                st.session_state.text_form_key += 1
                                st.rerun()
                            else:
                                st.error("❌ Failed to add text evidence. Please try again.")
                        except Exception as e:
                            st.error(f"❌ Error adding text evidence: {e}")
                            logger.error(f"Error adding text evidence: {e}")
                    else:
                        st.warning("⚠️ Please fill in both Title and Content fields.")
        
        st.markdown("---")
        

        is_dark = False
        

        if texts:

            from collections import defaultdict
            texts_by_type = defaultdict(list)
            for txt in texts:
                texts_by_type[txt.source_type].append(txt)
            

            type_labels = {
                "witness_statement": "🔍 Witness Statements",
                "forensic_report": "🧪 Forensic Reports",
                "cctv_video": "🎥 CCTV / Timeline Evidence",
                "timeline": "⏰ Timeline Evidence",
                "digital_evidence": "💻 Digital Evidence",
                "scene_notes": "📝 Scene Notes",
                "physical_object": "🔍 Physical Objects",
                "autopsy_report": "⚕️ Autopsy Reports",
                "alibi": "🛡️ Alibi Evidence",
                "other": "📄 Other Evidence"
            }
            

            for source_type, type_texts in texts_by_type.items():
                label = type_labels.get(source_type, f"📄 {source_type.replace('_', ' ').title()}")
                expanded = (source_type == "witness_statement" and len(type_texts) > 0)
                
                with st.expander(f"{label} ({len(type_texts)})", expanded=expanded):
                    for txt in type_texts:

                        render_evidence_card(txt, is_dark)
                        

                        st.markdown("---")
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown("**Full Content:**")
                            st.text_area(
                                "Content",
                                value=txt.content,
                                height=200,
                                disabled=True,
                                key=f"text_content_{txt.id}",
                                label_visibility="collapsed"
                            )
                        
                        with col2:
                            st.text(f"Type: {txt.source_type}")
                            st.text(f"Added: {txt.created_at.strftime('%Y-%m-%d %H:%M')}")
                            

                            delete_key = f"delete_text_{txt.id}"
                            if delete_key not in st.session_state:
                                st.session_state[delete_key] = False
                            
                            if st.button("🗑️ Delete", key=f"delete_btn_text_{txt.id}", type="secondary"):
                                st.session_state[delete_key] = True
                            
                            if st.session_state[delete_key]:
                                st.warning(f"⚠️ Delete '{txt.title}'?")
                                col_confirm, col_cancel = st.columns(2)
                                
                                with col_confirm:
                                    if st.button("✅ Confirm", key=f"confirm_delete_text_{txt.id}"):
                                        if delete_text_document(txt.id):
                                            st.success(f"✅ Deleted '{txt.title}'")
                                            st.session_state[delete_key] = False
                                            st.rerun()
                                        else:
                                            st.error("❌ Failed to delete document")
                                
                                with col_cancel:
                                    if st.button("❌ Cancel", key=f"cancel_delete_text_{txt.id}"):
                                        st.session_state[delete_key] = False
                                        st.rerun()
                        st.markdown("---")
        else:
            st.info("📄 No text documents yet. Use the form above to add witness statements, reports, or notes.")
        
        st.markdown("---")
        

        if images:
            with st.expander(f"🖼️ Image Evidence ({len(images)})", expanded=True):
                for img in images:

                    render_image_card(img, is_dark)
                    

                    st.markdown("---")

                    try:
                        from app.security.crypto_adapted import get_crypto_service
                        from io import BytesIO
                        
                        crypto_service = get_crypto_service()
                        decrypted_bytes = crypto_service.decrypt_file(img.file_path)
                        
                        st.image(
                            decrypted_bytes,
                            caption=img.filename,
                            use_column_width=True
                        )
                    except Exception as e:
                        st.error(f"⚠️ Could not load image: {e}")
                        logger.error(f"Error decrypting image {img.id}: {e}")
                    
                    st.markdown("---")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        if img.caption_text:
                            st.markdown("**Caption:**")
                            st.text(img.caption_text)
                        else:
                            st.info("Not yet analyzed")
                    
                    with col2:
                        st.text(f"Uploaded: {img.created_at.strftime('%Y-%m-%d %H:%M')}")
                        st.text(f"File: {img.filename}")
                    

                    col_analyze, col_delete = st.columns(2)
                    
                    with col_analyze:

                        if st.button(f"🔄 Re-analyze", key=f"reanalyze_{img.id}", use_container_width=True):
                            with st.spinner("Analyzing..."):
                                result = analyze_image(img.id)
                                if result:
                                    st.success("✅ Analysis complete!")
                                    st.rerun()
                    
                    with col_delete:

                        delete_key = f"delete_image_{img.id}"
                        if delete_key not in st.session_state:
                            st.session_state[delete_key] = False
                        
                        if st.button("🗑️ Delete", key=f"delete_btn_image_{img.id}", type="secondary", use_container_width=True):
                            st.session_state[delete_key] = True
                        
                        if st.session_state[delete_key]:
                            st.warning(f"⚠️ Delete '{img.filename}'?")
                            col_confirm, col_cancel = st.columns(2)
                            
                            with col_confirm:
                                if st.button("✅ Confirm", key=f"confirm_delete_image_{img.id}", use_container_width=True):
                                    if delete_image(img.id):
                                        st.success(f"✅ Deleted '{img.filename}'")
                                        st.session_state[delete_key] = False
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to delete image")
                            
                            with col_cancel:
                                if st.button("❌ Cancel", key=f"cancel_delete_image_{img.id}", use_container_width=True):
                                    st.session_state[delete_key] = False
                                    st.rerun()
                    

                    if img.exif_json:
                        st.markdown("**🔍 EXIF Metadata:**")
                        st.json(img.exif_json)
                    st.markdown("---")
        else:
            st.info("📸 No images yet. Use the sidebar to upload image evidence.")
            
    except Exception as e:
        logger.error(f"Error rendering evidence tab: {e}")
        st.error(f"Error loading evidence: {e}")


def render_suspects_tab(case_id: int):
    """Render suspects tab with correlation results"""
    st.subheader("🎯 Suspect Analysis")
    
    try:
        suspects = get_suspects_by_case(case_id)
        

        if 'success_messages' in st.session_state and st.session_state.success_messages:
            for msg in st.session_state.success_messages:
                st.success(msg)

            st.session_state.success_messages = []
        

        with st.expander("➕ Add New Suspect", expanded=len(suspects) == 0):

            with st.form(f"add_suspect_form_{st.session_state.suspect_form_key}"):
                st.markdown("**Create a new suspect for this case**")
                
                suspect_name = st.text_input(
                    "Suspect Name*",
                    placeholder="John Doe",
                    help="Full name of the suspect"
                )
                
                suspect_profile = st.text_area(
                    "Profile / Background*",
                    placeholder="Known associate, history of theft, seen near the scene...",
                    help="Detailed profile and background information",
                    height=100
                )
                
                st.markdown("**Optional Metadata (JSON)**")
                st.caption("Add structured metadata like vehicle, location, aliases, etc.")
                
                col1, col2 = st.columns(2)
                with col1:
                    vehicle = st.text_input("Vehicle", placeholder="Red Toyota Camry")
                    workplace = st.text_input("Workplace", placeholder="Downtown Bank")
                
                with col2:
                    alias = st.text_input("Alias", placeholder="Johnny")
                    phone = st.text_input("Phone", placeholder="+1-555-1234")
                
                submitted = st.form_submit_button("➕ Add Suspect", use_container_width=True)
                
                if submitted:
                    if suspect_name and suspect_profile:

                        metadata = {}
                        if vehicle:
                            metadata['vehicle'] = vehicle
                        if workplace:
                            metadata['workplace'] = workplace
                        if alias:
                            metadata['alias'] = alias
                        if phone:
                            metadata['phone'] = phone
                        

                        try:
                            from app.db import add_suspect
                            
                            new_suspect = add_suspect(
                                case_id=case_id,
                                name=suspect_name,
                                profile_text=suspect_profile,
                                metadata_json=metadata if metadata else None
                            )
                            
                            if new_suspect:

                                if 'success_messages' not in st.session_state:
                                    st.session_state.success_messages = []
                                st.session_state.success_messages.append(
                                    f"✅ Suspect '{suspect_name}' added successfully! (ID: {new_suspect.id})"
                                )
                                logger.info(f"Added suspect: {suspect_name} to case {case_id}")

                                st.session_state.suspect_form_key += 1
                                st.rerun()
                            else:
                                st.error("❌ Failed to add suspect. Please try again.")
                        except Exception as e:
                            st.error(f"❌ Error adding suspect: {e}")
                            logger.error(f"Error adding suspect: {e}")
                    else:
                        st.warning("⚠️ Please fill in both Name and Profile fields.")
        
        st.markdown("---")
        

        if not suspects:
            st.info("👆 Add your first suspect using the form above!")
        else:
            st.markdown(f"**{len(suspects)} suspect(s) on record:**")
            
            for suspect in suspects:
                with st.expander(f"👤 {suspect.name} (ID: {suspect.id})", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("**Profile:**")
                        st.text(suspect.profile_text)
                    
                    with col2:
                        st.text(f"Added: {suspect.created_at.strftime('%Y-%m-%d')}")
                    
                    if suspect.metadata_json:
                        st.markdown("**Metadata:**")
                        st.json(suspect.metadata_json)
        

        if suspects:
            st.markdown("---")
            

            if st.session_state.last_correlation_result:
                display_correlation_results(st.session_state.last_correlation_result)
            else:

                analysis_results = get_analysis_results(case_id)
                
                if analysis_results:

                    from collections import defaultdict
                    results_by_run = defaultdict(list)
                    for result in analysis_results:
                        results_by_run[result.run_at].append(result)
                    

                    if results_by_run:
                        latest_run_time = max(results_by_run.keys())
                        latest_results = results_by_run[latest_run_time]
                        

                        ranked = []
                        for result in latest_results:
                            suspect_name = next(
                                (s.name for s in suspects if s.id == result.suspect_id),
                                "Unknown"
                            )
                            


                            matched_clues = []
                            components = {
                                'base_sim': 0.0,
                                'keyword_score': 0.0,
                                'decisive_bonus': 0.0
                            }
                            contributing_docs = []
                            reasoning_trace = []
                            
                            if isinstance(result.matched_clues_json, dict):

                                if 'clues' in result.matched_clues_json:
                                    matched_clues = result.matched_clues_json['clues']
                                elif 'matched_clues' in result.matched_clues_json:
                                    matched_clues = result.matched_clues_json['matched_clues']
                                

                                if 'components' in result.matched_clues_json:
                                    saved_components = result.matched_clues_json['components']
                                    if isinstance(saved_components, dict):
                                        components = {
                                            'base_sim': saved_components.get('base_sim', 0.0),
                                            'keyword_score': saved_components.get('keyword_score', 0.0),
                                            'decisive_bonus': saved_components.get('decisive_bonus', 0.0)
                                        }
                                

                                if 'contributing_docs' in result.matched_clues_json:
                                    contributing_docs = result.matched_clues_json['contributing_docs']
                                    if not isinstance(contributing_docs, list):
                                        contributing_docs = []
                                

                                if 'reasoning_trace' in result.matched_clues_json:
                                    reasoning_trace = result.matched_clues_json['reasoning_trace']
                                    if not isinstance(reasoning_trace, list):
                                        reasoning_trace = []
                            elif isinstance(result.matched_clues_json, list):

                                matched_clues = result.matched_clues_json
                            
                            ranked.append({
                                'suspect_id': result.suspect_id,
                                'suspect_name': suspect_name,
                                'score': result.score_float,
                                'matched_clues': matched_clues,
                                'components': components,
                                'contributing_docs': contributing_docs,
                                'reasoning_trace': reasoning_trace
                            })
                        

                        ranked.sort(key=lambda x: x['score'], reverse=True)
                        

                        saved_result = {
                            'case_id': case_id,
                            'ranked': ranked,
                            'query': 'Saved analysis',
                            'docs_used': len(latest_results),
                            'persisted': True
                        }
                        
                        st.info(f"📊 Displaying saved correlation results from {latest_run_time.strftime('%Y-%m-%d %H:%M')}")
                        display_correlation_results(saved_result)
                    else:
                        st.info("👈 Click 'Correlate Evidence' in the sidebar to analyze suspects")
                else:
                    st.info("👈 Click 'Correlate Evidence' in the sidebar to analyze suspects")
        else:
            st.info("👈 Add suspects first, then click 'Correlate Evidence' in the sidebar")
        

        analysis_results = get_analysis_results(case_id)
        
        if analysis_results:
            st.markdown("---")
            st.markdown("### 📜 Analysis History")
            

            from collections import defaultdict
            runs_by_time = defaultdict(list)
            for result in analysis_results:
                runs_by_time[result.run_at].append(result)
            

            for run_time in sorted(runs_by_time.keys(), reverse=True)[:5]:
                run_results = runs_by_time[run_time]
                st.markdown(f"**{run_time.strftime('%Y-%m-%d %H:%M')}** ({len(run_results)} suspects)")
                for result in sorted(run_results, key=lambda x: x.score_float, reverse=True):
                    suspect_name = next(
                        (s.name for s in suspects if s.id == result.suspect_id),
                        "Unknown"
                    )
                    st.text(f"  • {suspect_name}: {result.score_float:.3f}")
        
    except Exception as e:
        logger.error(f"Error rendering suspects tab: {e}")
        st.error(f"Error loading suspects: {e}")


def render_agent_tab(case_id: int):
    """Render agent Q&A tab"""
    st.subheader("🤖 Ask the AI Agent")
    
    st.markdown("""
    Ask questions about the case evidence. The agent will:
    - Search relevant evidence using semantic search
    - Provide answers with citations
    - Rank suspects when appropriate
    - Apply ethical guardrails
    - Use custom tools (case summary, timeline analysis) when needed
    """)
    

    with st.form("agent_query_form"):
        user_query = st.text_area(
            "Your Question",
            placeholder="Who is the most likely suspect? What evidence do we have about the red car?",
            height=100
        )
        
        submitted = st.form_submit_button("🚀 Ask Agent", use_container_width=True)
    
    if submitted and user_query:
        try:
            with st.spinner("🤔 Agent is thinking..."):
                logger.info(f"Agent query for case {case_id}: {user_query}")

                user_id = st.session_state.get('user_id', None)

                result = answer_question(case_id=case_id, user_query=user_query, k=None, user_id=user_id)
                
                if result:

                    st.session_state.conversation_history.append({
                        'query': user_query,
                        'result': result,
                        'timestamp': datetime.now()
                    })
                    
                    logger.info(f"Agent response: {result.get('answer', '')[:100]}...")
                    

                    display_agent_response(result)
                else:
                    st.error("No response from agent")
        
        except Exception as e:
            logger.error(f"Error querying agent: {e}", exc_info=True)
            st.error(f"❌ Error: {e}")
    

    if st.session_state.conversation_history:
        st.markdown("---")
        st.markdown("### 💬 Conversation History")
        
        for idx, conv in enumerate(reversed(st.session_state.conversation_history[-5:]), 1):
            with st.expander(
                f"Q{len(st.session_state.conversation_history) - idx + 1}: {conv['query'][:60]}...",
                expanded=(idx == 1)
            ):
                st.markdown(f"**Question:** {conv['query']}")
                st.markdown(f"**Answer:** {conv['result'].get('answer', 'No answer')[:300]}...")
                st.caption(f"Asked: {conv['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")






def main():
    """Main application entry point"""
    

    init_session_state()
    

    if not validate_configuration():
        st.stop()
    

    try:
        config.ensure_directories()
    except Exception as e:
        st.error(f"❌ Error creating directories: {e}")
        st.stop()
    

    try:
        from app.db import test_connection, get_engine
        engine = get_engine()
        if not test_connection(engine):
            st.sidebar.error("❌ Database connection failed")
            st.error("""
            ❌ **Database Connection Failed**
            
            Please ensure:
            1. PostgreSQL is running
            2. DATABASE_URL in .env is correct
            3. Database schema is initialized (`python -m app.db.init_db`)
            """)
            st.stop()
    except Exception as e:
        st.sidebar.warning("⚠️ Could not verify database connection")
        logger.warning(f"Database check failed: {e}")
    

    try:
        selected_case_id = render_sidebar()
        render_main_content(selected_case_id)
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        st.error(f"❌ Application Error: {e}")
        
        with st.expander("🐛 Debug Info"):
            st.code(str(e))
    

    st.markdown("---")
    st.caption("🕵️ Forensic Crime Analysis Agent | Built with Streamlit + LangChain + Gemini Pro")


if __name__ == "__main__":
    main()

