"""
Database ORM models for Forensic Crime Analysis Agent
Uses SQLAlchemy 2.x with type hints and relationships
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all ORM models"""
    pass


class Case(Base):
    """
    Represents a forensic investigation case
    
    Attributes:
        id: Primary key
        title: Case title/name
        description: Detailed case description
        created_at: Timestamp when case was created
        suspects: Related suspects
        text_documents: Related text documents
        images: Related evidence images
        analysis_results: Related analysis results
    """
    __tablename__ = "cases"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    

    suspects: Mapped[List["Suspect"]] = relationship(
        "Suspect", 
        back_populates="case",
        cascade="all, delete-orphan"
    )
    text_documents: Mapped[List["TextDocument"]] = relationship(
        "TextDocument",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    images: Mapped[List["Image"]] = relationship(
        "Image",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    analysis_results: Mapped[List["AnalysisResult"]] = relationship(
        "AnalysisResult",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Case(id={self.id}, title='{self.title}', created_at={self.created_at})>"


class Suspect(Base):
    """
    Represents a suspect in a case
    
    Attributes:
        id: Primary key
        case_id: Foreign key to Case
        name: Suspect's name
        profile_text: Detailed profile/background information
        metadata_json: Additional metadata (alibi, contacts, etc.)
        created_at: Timestamp when suspect was added
        case: Related case object
        analysis_results: Related analysis results
    """
    __tablename__ = "suspects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    

    case: Mapped["Case"] = relationship("Case", back_populates="suspects")
    analysis_results: Mapped[List["AnalysisResult"]] = relationship(
        "AnalysisResult",
        back_populates="suspect",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Suspect(id={self.id}, name='{self.name}', case_id={self.case_id})>"


class TextDocument(Base):
    """
    Represents a text document (witness statement, report, note)
    
    Attributes:
        id: Primary key
        case_id: Foreign key to Case
        source_type: Type of document (witness, report, note, etc.)
        title: Document title
        content: Full text content
        created_at: Timestamp when document was added
        case: Related case object
    """
    __tablename__ = "text_documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    

    case: Mapped["Case"] = relationship("Case", back_populates="text_documents")
    
    def __repr__(self) -> str:
        return f"<TextDocument(id={self.id}, title='{self.title}', source_type='{self.source_type}')>"


class Image(Base):
    """
    Represents an encrypted evidence image
    
    Attributes:
        id: Primary key
        case_id: Foreign key to Case
        filename: Original filename
        file_path: Path to encrypted file on disk
        iv_hex: Initialization vector for AES encryption (hex)
        sha256_hex: SHA-256 hash of original file (hex)
        exif_json: Extracted EXIF metadata (from Image Analyzer tool)
        caption_text: AI-generated caption (from Image Analyzer tool)
        created_at: Timestamp when image was added
        case: Related case object
    """
    __tablename__ = "images"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    iv_hex: Mapped[str] = mapped_column(String(32), nullable=False)
    sha256_hex: Mapped[str] = mapped_column(String(64), nullable=False)
    exif_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    caption_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    

    case: Mapped["Case"] = relationship("Case", back_populates="images")
    
    def __repr__(self) -> str:
        return f"<Image(id={self.id}, filename='{self.filename}', case_id={self.case_id})>"


class AnalysisResult(Base):
    """
    Represents an evidence correlation analysis result
    
    Attributes:
        id: Primary key
        case_id: Foreign key to Case
        suspect_id: Foreign key to Suspect
        score_float: Correlation score (0.0 - 1.0)
        matched_clues_json: Dictionary of matched evidence and reasoning
        run_at: Timestamp when analysis was run
        case: Related case object
        suspect: Related suspect object
    """
    __tablename__ = "analysis_results"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False
    )
    suspect_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("suspects.id", ondelete="CASCADE"),
        nullable=False
    )
    score_float: Mapped[float] = mapped_column(Float, nullable=False)
    matched_clues_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    

    case: Mapped["Case"] = relationship("Case", back_populates="analysis_results")
    suspect: Mapped["Suspect"] = relationship("Suspect", back_populates="analysis_results")
    
    def __repr__(self) -> str:
        return (f"<AnalysisResult(id={self.id}, suspect_id={self.suspect_id}, "
                f"score={self.score_float:.2f}, run_at={self.run_at})>")


class PolarityCache(Base):
    """
    Caches LLM polarity classifications for decisive evidence sentences
    
    This ensures:
    - Never pay for the same LLM call twice
    - Evidence stays consistent across runs
    - Rebuilding index becomes faster
    - Correlation becomes faster
    - Re-running cases produces identical results (forensic reproducibility)
    
    Attributes:
        id: Primary key
        suspect: Suspect name
        term: Decisive term found in sentence
        sentence: The sentence text (normalized)
        polarity: Classification result ("positive", "negative", or "neutral")
        created_at: Timestamp when classification was cached
    """
    __tablename__ = "polarity_cache"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    suspect: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    term: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    polarity: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return (f"<PolarityCache(id={self.id}, suspect='{self.suspect}', "
                f"term='{self.term}', polarity='{self.polarity}')>")


class TimelineEvent(Base):
    """
    Represents a timeline event extracted from evidence documents
    
    This table stores time-based events (arrivals, departures, sightings, etc.)
    extracted from text evidence using LLM-based extraction. Events are used
    for timeline analysis, contradiction detection, and suspect scoring.
    
    Attributes:
        id: Primary key
        case_id: Foreign key to Case
        suspect_id: Foreign key to Suspect (nullable if suspect not identified)
        source_doc_id: Source document identifier (e.g., "text_3", "image_1")
        raw_text: The original sentence containing the event
        event_type: Type of event (arrival, departure, seen, left, argument, sound, CCTV capture, etc.)
        timestamp: Normalized timestamp of the event
        confidence: Confidence score (0.0-1.0) for the extraction
        created_at: Timestamp when event was extracted
    """
    __tablename__ = "timeline_events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    suspect_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("suspects.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    source_doc_id: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return (f"<TimelineEvent(id={self.id}, case_id={self.case_id}, "
                f"event_type='{self.event_type}', timestamp={self.timestamp})>")


class ChatMemory(Base):
    """
    Stores long-term memory for users in the forensic chatbot
    
    This table stores user personal preferences and information that persists
    across sessions. Memory is user-specific and should NOT contain sensitive
    case evidence or suspect information - only user personal details.
    
    Attributes:
        id: Primary key
        user_id: User identifier (string) - unique per user session
        key: Memory key (e.g., "name", "location", "birthday")
        value: Memory value (e.g., "Sami", "Beirut", "May 2")
        created_at: Timestamp when memory was created
        updated_at: Timestamp when memory was last updated
    """
    __tablename__ = "chat_memory"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    

    __table_args__ = (
        UniqueConstraint('user_id', 'key', name='uq_chat_memory_user_key'),
    )
    
    def __repr__(self) -> str:
        return (f"<ChatMemory(id={self.id}, user_id='{self.user_id}', "
                f"key='{self.key}', value='{self.value[:30]}...')>")


class ChatHistory(Base):
    """
    Stores chat conversation history for users
    
    This table stores each message exchange between the user and the chatbot,
    allowing the agent to reference past conversation turns for context.
    
    Attributes:
        id: Primary key
        case_id: Foreign key to Case (optional, for case-specific chats)
        user_id: User identifier (string)
        message: The message text
        is_user: True if message is from user, False if from bot
        timestamp: Timestamp when message was sent
    """
    __tablename__ = "chat_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_user: Mapped[bool] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return (f"<ChatHistory(id={self.id}, user_id='{self.user_id}', "
                f"is_user={self.is_user}, message='{self.message[:30]}...')>")