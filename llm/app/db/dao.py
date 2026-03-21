"""
Data Access Object (DAO) for Forensic Crime Analysis Agent
Provides clean interface for database CRUD operations with error handling
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.sql import func

from app.db.models import Case, Suspect, TextDocument, Image, AnalysisResult, PolarityCache, TimelineEvent, ChatMemory, ChatHistory
from app.db.init_db import get_session_factory


logger = logging.getLogger(__name__)


SessionLocal = get_session_factory()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions
    Automatically handles commit/rollback and cleanup
    
    Yields:
        SQLAlchemy Session
        
    Example:
        with get_db_session() as session:
            case = session.query(Case).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Session rolled back due to error: {e}")
        raise
    finally:
        session.close()






def add_case(title: str, description: str) -> Optional[Case]:
    """
    Create a new forensic case
    
    Args:
        title: Case title/name
        description: Detailed case description
        
    Returns:
        Created Case object, or None if failed
    """
    try:
        with get_db_session() as session:
            case = Case(
                title=title,
                description=description
            )
            session.add(case)
            session.flush()
            session.refresh(case)
            session.expunge(case)
            
            logger.info(f"✅ Created case: {case}")
            return case
            
    except IntegrityError as e:
        logger.error(f"❌ Integrity error creating case: {e}")
        return None
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error creating case: {e}")
        return None


def get_case(case_id: int) -> Optional[Case]:
    """
    Retrieve a case by ID
    
    Args:
        case_id: Case ID
        
    Returns:
        Case object, or None if not found
    """
    try:
        with get_db_session() as session:
            case = session.query(Case).filter(Case.id == case_id).first()
            if case:

                _ = case.suspects
                _ = case.text_documents
                _ = case.images
                _ = case.analysis_results
                session.expunge(case)
            return case
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error retrieving case {case_id}: {e}")
        return None


def get_all_cases() -> List[Case]:
    """
    Retrieve all cases
    
    Returns:
        List of Case objects
    """
    try:
        with get_db_session() as session:
            cases = session.query(Case).order_by(Case.created_at.desc()).all()
            for case in cases:
                session.expunge(case)
            return cases
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error retrieving cases: {e}")
        return []






def add_suspect(
    case_id: int,
    name: str,
    profile_text: str,
    metadata_json: Optional[Dict[str, Any]] = None
) -> Optional[Suspect]:
    """
    Add a suspect to a case
    
    Args:
        case_id: Case ID
        name: Suspect's name
        profile_text: Detailed profile/background
        metadata_json: Additional metadata (alibi, contacts, etc.)
        
    Returns:
        Created Suspect object, or None if failed
    """
    try:
        with get_db_session() as session:
            suspect = Suspect(
                case_id=case_id,
                name=name,
                profile_text=profile_text,
                metadata_json=metadata_json or {}
            )
            session.add(suspect)
            session.flush()
            session.refresh(suspect)
            session.expunge(suspect)
            
            logger.info(f"✅ Added suspect: {suspect}")
            return suspect
            
    except IntegrityError as e:
        logger.error(f"❌ Integrity error adding suspect (case_id={case_id} may not exist): {e}")
        return None
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error adding suspect: {e}")
        return None


def get_suspects_by_case(case_id: int) -> List[Suspect]:
    """
    Retrieve all suspects for a case
    
    Args:
        case_id: Case ID
        
    Returns:
        List of Suspect objects
    """
    try:
        with get_db_session() as session:
            suspects = session.query(Suspect).filter(
                Suspect.case_id == case_id
            ).order_by(Suspect.created_at).all()
            for suspect in suspects:
                session.expunge(suspect)
            return suspects
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error retrieving suspects for case {case_id}: {e}")
        return []






def add_text(
    case_id: int,
    source_type: str,
    title: str,
    content: str
) -> Optional[TextDocument]:
    """
    Add a text document to a case
    
    Args:
        case_id: Case ID
        source_type: Type of document (witness, report, note, etc.)
        title: Document title
        content: Full text content
        
    Returns:
        Created TextDocument object, or None if failed
    """
    try:
        with get_db_session() as session:
            text_doc = TextDocument(
                case_id=case_id,
                source_type=source_type,
                title=title,
                content=content
            )
            session.add(text_doc)
            session.flush()
            session.refresh(text_doc)
            session.expunge(text_doc)
            
            logger.info(f"✅ Added text document: {text_doc}")
            





            
            return text_doc
            
    except IntegrityError as e:
        logger.error(f"❌ Integrity error adding text document: {e}")
        return None
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error adding text document: {e}")
        return None


def get_texts_by_case(case_id: int) -> List[TextDocument]:
    """
    Retrieve all text documents for a case
    
    Args:
        case_id: Case ID
        
    Returns:
        List of TextDocument objects
    """
    try:
        with get_db_session() as session:
            texts = session.query(TextDocument).filter(
                TextDocument.case_id == case_id
            ).order_by(TextDocument.created_at).all()
            for text in texts:
                session.expunge(text)
            return texts
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error retrieving texts for case {case_id}: {e}")
        return []


def delete_text_document(text_id: int) -> bool:
    """
    Delete a text document from the database
    
    Args:
        text_id: Text document ID
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        with get_db_session() as session:
            text_doc = session.query(TextDocument).filter(TextDocument.id == text_id).first()
            
            if not text_doc:
                logger.warning(f"⚠️ Text document {text_id} not found")
                return False
            
            title = text_doc.title
            session.delete(text_doc)
            session.flush()
            
            logger.info(f"✅ Deleted text document: {title} (ID: {text_id})")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error deleting text document {text_id}: {e}")
        return False






def add_image(
    case_id: int,
    filename: str,
    file_path: str,
    iv_hex: str,
    sha256_hex: str
) -> Optional[Image]:
    """
    Add an encrypted image to a case
    
    Args:
        case_id: Case ID
        filename: Original filename
        file_path: Path to encrypted file
        iv_hex: Initialization vector (hex string)
        sha256_hex: SHA-256 hash of original file (hex string)
        
    Returns:
        Created Image object, or None if failed
    """
    try:
        with get_db_session() as session:
            image = Image(
                case_id=case_id,
                filename=filename,
                file_path=file_path,
                iv_hex=iv_hex,
                sha256_hex=sha256_hex
            )
            session.add(image)
            session.flush()
            session.refresh(image)
            session.expunge(image)
            
            logger.info(f"✅ Added image: {image}")
            return image
            
    except IntegrityError as e:
        logger.error(f"❌ Integrity error adding image (file_path must be unique): {e}")
        return None
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error adding image: {e}")
        return None


def update_image_analysis(
    image_id: int,
    exif_json: Optional[Dict[str, Any]] = None,
    caption_text: Optional[str] = None
) -> bool:
    """
    Update image with analysis results (EXIF data and AI caption)
    
    Args:
        image_id: Image ID
        exif_json: Extracted EXIF metadata
        caption_text: AI-generated caption
        
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        with get_db_session() as session:
            image = session.query(Image).filter(Image.id == image_id).first()
            
            if not image:
                logger.error(f"❌ Image {image_id} not found")
                return False
            
            if exif_json is not None:
                image.exif_json = exif_json
            if caption_text is not None:
                image.caption_text = caption_text
            
            session.flush()
            logger.info(f"✅ Updated image analysis: {image}")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error updating image analysis: {e}")
        return False


def get_images_by_case(case_id: int) -> List[Image]:
    """
    Retrieve all images for a case
    
    Args:
        case_id: Case ID
        
    Returns:
        List of Image objects
    """
    try:
        with get_db_session() as session:
            images = session.query(Image).filter(
                Image.case_id == case_id
            ).order_by(Image.created_at).all()
            for image in images:
                session.expunge(image)
            return images
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error retrieving images for case {case_id}: {e}")
        return []


def delete_image(image_id: int) -> bool:
    """
    Delete an image from the database and remove the encrypted file from disk
    
    Args:
        image_id: Image ID
        
    Returns:
        True if deleted successfully, False otherwise
    """
    import os
    from pathlib import Path
    
    try:
        with get_db_session() as session:
            image = session.query(Image).filter(Image.id == image_id).first()
            
            if not image:
                logger.warning(f"⚠️ Image {image_id} not found")
                return False
            

            file_path = image.file_path
            filename = image.filename
            

            session.delete(image)
            session.flush()
            
            logger.info(f"✅ Deleted image from database: {filename} (ID: {image_id})")
            

            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"✅ Deleted encrypted file: {file_path}")
                except OSError as e:
                    logger.warning(f"⚠️ Could not delete file {file_path}: {e}")

            
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error deleting image {image_id}: {e}")
        return False






def save_analysis_results(case_id: int, results: List[Dict[str, Any]]) -> bool:
    """
    Save evidence correlation analysis results for multiple suspects
    
    Args:
        case_id: Case ID
        results: List of result dictionaries, each containing:
            - suspect_id: int
            - score: float (0.0-1.0)
            - matched_clues: dict
            
    Returns:
        True if saved successfully, False otherwise
        
    Example:
        results = [
            {
                "suspect_id": 1,
                "score": 0.85,
                "matched_clues": {
                    "location": "Found near crime scene",
                    "timeline": "No alibi for time of crime"
                }
            },
            {
                "suspect_id": 2,
                "score": 0.32,
                "matched_clues": {
                    "witness": "Not mentioned in statements"
                }
            }
        ]
        save_analysis_results(case_id=1, results=results)
    """
    try:
        with get_db_session() as session:
            for result_data in results:
                analysis = AnalysisResult(
                    case_id=case_id,
                    suspect_id=result_data["suspect_id"],
                    score_float=result_data["score"],
                    matched_clues_json=result_data["matched_clues"]
                )
                session.add(analysis)
            
            session.flush()
            logger.info(f"✅ Saved {len(results)} analysis results for case {case_id}")
            return True
            
    except IntegrityError as e:
        logger.error(f"❌ Integrity error saving analysis results: {e}")
        return False
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error saving analysis results: {e}")
        return False
    except KeyError as e:
        logger.error(f"❌ Missing required field in results: {e}")
        return False


def get_analysis_results(case_id: int) -> List[AnalysisResult]:
    """
    Retrieve analysis results for a case, ordered by score (highest first)
    
    Args:
        case_id: Case ID
        
    Returns:
        List of AnalysisResult objects
    """
    try:
        with get_db_session() as session:
            results = session.query(AnalysisResult).filter(
                AnalysisResult.case_id == case_id
            ).order_by(AnalysisResult.score_float.desc()).all()
            for result in results:
                session.expunge(result)
            return results
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error retrieving analysis results: {e}")
        return []






def get_case_data(case_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve complete case data including all related entities
    
    Args:
        case_id: Case ID
        
    Returns:
        Dictionary containing all case data, or None if case not found
        
    Structure:
        {
            "case": {...},
            "suspects": [...],
            "text_documents": [...],
            "images": [...],
            "analysis_results": [...]
        }
    """
    try:
        case = get_case(case_id)
        
        if not case:
            logger.warning(f"Case {case_id} not found")
            return None
        

        suspect_names = {s.id: s.name for s in case.suspects}
        

        case_data = {
            "case": {
                "id": case.id,
                "title": case.title,
                "description": case.description,
                "created_at": case.created_at.isoformat()
            },
            "suspects": [
                {
                    "id": s.id,
                    "name": s.name,
                    "profile_text": s.profile_text,
                    "metadata": s.metadata_json,
                    "created_at": s.created_at.isoformat()
                }
                for s in case.suspects
            ],
            "text_documents": [
                {
                    "id": t.id,
                    "source_type": t.source_type,
                    "title": t.title,
                    "content": t.content,
                    "created_at": t.created_at.isoformat()
                }
                for t in case.text_documents
            ],
            "images": [
                {
                    "id": i.id,
                    "filename": i.filename,
                    "file_path": i.file_path,
                    "sha256": i.sha256_hex,
                    "exif": i.exif_json,
                    "caption": i.caption_text,
                    "created_at": i.created_at.isoformat()
                }
                for i in case.images
            ],
            "analysis_results": [
                {
                    "id": a.id,
                    "suspect_id": a.suspect_id,
                    "suspect_name": suspect_names.get(a.suspect_id, "Unknown"),
                    "score": a.score_float,
                    "matched_clues": a.matched_clues_json,
                    "run_at": a.run_at.isoformat()
                }
                for a in case.analysis_results
            ]
        }
        
        logger.info(f"✅ Retrieved complete data for case {case_id}")
        return case_data
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error retrieving case data: {e}")
        return None


def delete_case(case_id: int) -> bool:
    """
    Delete a case and all related data (cascade delete)
    
    Args:
        case_id: Case ID
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        with get_db_session() as session:
            case = session.query(Case).filter(Case.id == case_id).first()
            
            if not case:
                logger.warning(f"Case {case_id} not found")
                return False
            
            session.delete(case)
            session.flush()
            
            logger.info(f"✅ Deleted case {case_id} and all related data")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error deleting case: {e}")
        return False






def get_cached_polarity(suspect: str, term: str, sentence: str) -> Optional[str]:
    """
    Retrieve cached polarity classification for a decisive evidence sentence
    
    Args:
        suspect: Suspect name
        term: Decisive term found in sentence
        sentence: The sentence text (will be normalized for lookup)
        
    Returns:
        Cached polarity ("positive", "negative", or "neutral"), or None if not cached
        
    Example:
        >>> polarity = get_cached_polarity("John Doe", "cctv", "CCTV shows John Doe entering")
        >>> print(polarity)  # "positive" or None
    """
    try:

        sentence_normalized = sentence.strip()
        
        with get_db_session() as session:
            entry = session.query(PolarityCache).filter_by(
                suspect=suspect,
                term=term,
                sentence=sentence_normalized
            ).first()
            
            if entry:
                logger.debug(
                    f"✅ Cache hit: polarity='{entry.polarity}' for suspect='{suspect}', "
                    f"term='{term}', sentence='{sentence_normalized[:60]}...'"
                )
                return entry.polarity
            
            return None
            
    except SQLAlchemyError as e:
        logger.warning(f"⚠️ Database error retrieving cached polarity: {e}")
        return None


def save_polarity_cache(suspect: str, term: str, sentence: str, polarity: str) -> bool:
    """
    Save polarity classification to cache
    
    Args:
        suspect: Suspect name
        term: Decisive term found in sentence
        sentence: The sentence text (will be normalized before saving)
        polarity: Classification result ("positive", "negative", or "neutral")
        
    Returns:
        True if saved successfully, False otherwise
        
    Example:
        >>> success = save_polarity_cache("John Doe", "cctv", "CCTV shows John Doe entering", "positive")
        >>> print(success)  # True
    """
    try:

        sentence_normalized = sentence.strip()
        

        if polarity not in ("positive", "negative", "neutral"):
            logger.warning(f"⚠️ Invalid polarity '{polarity}' - not caching")
            return False
        
        with get_db_session() as session:

            existing = session.query(PolarityCache).filter_by(
                suspect=suspect,
                term=term,
                sentence=sentence_normalized
            ).first()
            
            if existing:

                existing.polarity = polarity
                logger.debug(f"✅ Updated cached polarity for suspect='{suspect}', term='{term}'")
            else:

                entry = PolarityCache(
                    suspect=suspect,
                    term=term,
                    sentence=sentence_normalized,
                    polarity=polarity
                )
                session.add(entry)
                logger.debug(
                    f"✅ Cached polarity: '{polarity}' for suspect='{suspect}', "
                    f"term='{term}', sentence='{sentence_normalized[:60]}...'"
                )
            
            session.flush()
            return True
            
    except IntegrityError as e:
        logger.warning(f"⚠️ Integrity error saving polarity cache: {e}")
        return False
    except SQLAlchemyError as e:
        logger.warning(f"⚠️ Database error saving polarity cache: {e}")
        return False






def add_timeline_event(event_dict: Dict[str, Any]) -> Optional[TimelineEvent]:
    """
    Add a timeline event to the database
    
    Args:
        event_dict: Dictionary containing event data:
            - case_id: Case ID
            - suspect_id: Suspect ID (optional)
            - source_doc_id: Source document ID (e.g., "text_3")
            - raw_text: Original sentence
            - event_type: Type of event
            - timestamp: Event timestamp (ISO format string or datetime)
            - confidence: Confidence score (0.0-1.0)
        
    Returns:
        Created TimelineEvent object, or None if failed
        
    Example:
        >>> event = add_timeline_event({
        ...     "case_id": 1,
        ...     "suspect_id": 2,
        ...     "source_doc_id": "text_3",
        ...     "raw_text": "John Doe left the bar at 9:45 PM",
        ...     "event_type": "departure",
        ...     "timestamp": "2025-11-12 21:45:00",
        ...     "confidence": 0.95
        ... })
    """
    try:
        from datetime import datetime
        

        timestamp = event_dict.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:

                try:
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logger.warning(f"Could not parse timestamp: {timestamp}")
                    return None
        
        with get_db_session() as session:
            event = TimelineEvent(
                case_id=event_dict["case_id"],
                suspect_id=event_dict.get("suspect_id"),
                source_doc_id=event_dict["source_doc_id"],
                raw_text=event_dict["raw_text"],
                event_type=event_dict["event_type"],
                timestamp=timestamp,
                confidence=event_dict.get("confidence", 1.0)
            )
            session.add(event)
            session.flush()
            session.refresh(event)
            session.expunge(event)
            
            logger.debug(f"✅ Added timeline event: {event}")
            return event
            
    except KeyError as e:
        logger.error(f"❌ Missing required field in event_dict: {e}")
        return None
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error adding timeline event: {e}")
        return None


def get_timeline_events(case_id: int, suspect_id: Optional[int] = None) -> List[TimelineEvent]:
    """
    Retrieve timeline events for a case, optionally filtered by suspect
    
    Args:
        case_id: Case ID
        suspect_id: Optional suspect ID to filter by
        
    Returns:
        List of TimelineEvent objects, sorted by timestamp
    """
    try:
        with get_db_session() as session:
            query = session.query(TimelineEvent).filter(
                TimelineEvent.case_id == case_id
            )
            
            if suspect_id is not None:
                query = query.filter(TimelineEvent.suspect_id == suspect_id)
            
            events = query.order_by(TimelineEvent.timestamp).all()
            
            for event in events:
                session.expunge(event)
            
            return events
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error retrieving timeline events: {e}")
        return []


def delete_timeline_events(case_id: int) -> bool:
    """
    Delete all timeline events for a case
    
    Args:
        case_id: Case ID
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        with get_db_session() as session:
            deleted_count = session.query(TimelineEvent).filter(
                TimelineEvent.case_id == case_id
            ).delete()
            
            session.flush()
            logger.info(f"✅ Deleted {deleted_count} timeline events for case {case_id}")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error deleting timeline events: {e}")
        return False






def save_memory(user_id: str, key: str, value: str) -> bool:
    """
    Save or update a memory entry for a user
    
    Creates a new memory entry if it doesn't exist, or updates the existing one
    if the user_id + key combination already exists.
    
    Args:
        user_id: User identifier (string)
        key: Memory key (e.g., "name", "location", "birthday")
        value: Memory value (e.g., "Sami", "Beirut", "May 2")
        
    Returns:
        True if saved successfully, False otherwise
        
    Example:
        >>> save_memory("user_123", "name", "Sami")
        True
        >>> save_memory("user_123", "location", "Beirut")
        True
    """
    try:
        with get_db_session() as session:

            existing = session.query(ChatMemory).filter_by(
                user_id=user_id,
                key=key
            ).first()
            
            if existing:

                existing.value = value
                existing.updated_at = func.now()
                logger.info(f"✅ Updated memory: user_id='{user_id}', key='{key}'")
            else:

                memory = ChatMemory(
                    user_id=user_id,
                    key=key,
                    value=value
                )
                session.add(memory)
                logger.info(f"✅ Created memory: user_id='{user_id}', key='{key}', value='{value[:30]}...'")
            
            session.flush()
            return True
            
    except IntegrityError as e:
        logger.error(f"❌ Integrity error saving memory: {e}")
        return False
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error saving memory: {e}")
        return False


def get_memory(user_id: str, key: str) -> Optional[str]:
    """
    Retrieve a specific memory value for a user
    
    Args:
        user_id: User identifier (string)
        key: Memory key to retrieve
        
    Returns:
        Memory value as string, or None if not found
        
    Example:
        >>> name = get_memory("user_123", "name")
        >>> print(name)  # "Sami" or None
    """
    try:
        with get_db_session() as session:
            memory = session.query(ChatMemory).filter_by(
                user_id=user_id,
                key=key
            ).first()
            
            if memory:
                logger.debug(f"✅ Retrieved memory: user_id='{user_id}', key='{key}'")
                return memory.value
            
            return None
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error retrieving memory: {e}")
        return None


def load_all_memory(user_id: str) -> Dict[str, str]:
    """
    Load all memory entries for a user as a dictionary
    
    Args:
        user_id: User identifier (string)
        
    Returns:
        Dictionary mapping memory keys to values
        
    Example:
        >>> memory = load_all_memory("user_123")
        >>> print(memory)  # {"name": "Sami", "location": "Beirut", "birthday": "May 2"}
    """
    try:
        with get_db_session() as session:
            memories = session.query(ChatMemory).filter_by(
                user_id=user_id
            ).all()
            
            result = {memory.key: memory.value for memory in memories}
            logger.debug(f"✅ Loaded {len(result)} memory entries for user_id='{user_id}'")
            return result
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error loading memory: {e}")
        return {}






def save_chat_message(
    user_id: str,
    message: str,
    is_user: bool,
    case_id: Optional[int] = None
) -> Optional[ChatHistory]:
    """
    Save a chat message to conversation history
    
    Args:
        user_id: User identifier (string)
        message: The message text
        is_user: True if message is from user, False if from bot
        case_id: Optional case ID for case-specific chats
        
    Returns:
        Created ChatHistory object, or None if failed
        
    Example:
        >>> save_chat_message("user_123", "What is my name?", True, case_id=1)
        >>> save_chat_message("user_123", "Your name is Sami.", False, case_id=1)
    """
    try:
        with get_db_session() as session:
            chat_entry = ChatHistory(
                user_id=user_id,
                message=message,
                is_user=is_user,
                case_id=case_id
            )
            session.add(chat_entry)
            session.flush()
            session.refresh(chat_entry)
            session.expunge(chat_entry)
            
            logger.debug(f"✅ Saved chat message: user_id='{user_id}', is_user={is_user}")
            return chat_entry
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error saving chat message: {e}")
        return None


def get_chat_history(
    user_id: str,
    case_id: Optional[int] = None,
    limit: Optional[int] = None
) -> List[ChatHistory]:
    """
    Retrieve chat history for a user, optionally filtered by case
    
    Args:
        user_id: User identifier (string)
        case_id: Optional case ID to filter by
        limit: Optional limit on number of messages to return (most recent first)
        
    Returns:
        List of ChatHistory objects, ordered by timestamp (most recent first)
        
    Example:
        >>> history = get_chat_history("user_123", case_id=1, limit=10)
        >>> for msg in history:
        ...     print(f"{'User' if msg.is_user else 'Bot'}: {msg.message}")
    """
    try:
        with get_db_session() as session:
            query = session.query(ChatHistory).filter_by(
                user_id=user_id
            )
            
            if case_id is not None:
                query = query.filter_by(case_id=case_id)
            
            query = query.order_by(ChatHistory.timestamp.desc())
            
            if limit is not None:
                query = query.limit(limit)
            
            messages = query.all()
            
            for msg in messages:
                session.expunge(msg)
            
            logger.debug(f"✅ Retrieved {len(messages)} chat messages for user_id='{user_id}'")
            return messages
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error retrieving chat history: {e}")
        return []

