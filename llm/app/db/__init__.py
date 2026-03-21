"""
Database models and management for PostgreSQL

Exports:
    - Models: Case, Suspect, TextDocument, Image, AnalysisResult
    - DAO functions: add_case, add_suspect, add_text, add_image, etc.
    - Initialization: init_db, reset_db, get_engine, get_session_factory
"""

from app.db.models import (
    Base,
    Case,
    Suspect,
    TextDocument,
    Image,
    AnalysisResult,
    PolarityCache,
    TimelineEvent,
    ChatMemory,
    ChatHistory
)

from app.db.init_db import (
    init_db,
    reset_db,
    get_engine,
    get_session_factory,
    test_connection
)

from app.db.dao import (

    get_db_session,
    

    add_case,
    get_case,
    get_all_cases,
    delete_case,
    

    add_suspect,
    get_suspects_by_case,
    

    add_text,
    get_texts_by_case,
    delete_text_document,
    

    add_image,
    update_image_analysis,
    get_images_by_case,
    delete_image,
    

    save_analysis_results,
    get_analysis_results,
    

    get_case_data,
    

    get_cached_polarity,
    save_polarity_cache,
    

    add_timeline_event,
    get_timeline_events,
    delete_timeline_events,
    

    save_memory,
    get_memory,
    load_all_memory,
    

    save_chat_message,
    get_chat_history
)

__all__ = [

    "Base",
    "Case",
    "Suspect",
    "TextDocument",
    "Image",
    "AnalysisResult",
    "PolarityCache",
    "TimelineEvent",
    "ChatMemory",
    "ChatHistory",
    

    "init_db",
    "reset_db",
    "get_engine",
    "get_session_factory",
    "test_connection",
    

    "get_db_session",
    

    "add_case",
    "get_case",
    "get_all_cases",
    "delete_case",
    "add_suspect",
    "get_suspects_by_case",
    "add_text",
    "get_texts_by_case",
    "delete_text_document",
    "add_image",
    "update_image_analysis",
    "get_images_by_case",
    "delete_image",
    "save_analysis_results",
    "get_analysis_results",
    "get_case_data",
    "get_cached_polarity",
    "save_polarity_cache",
    "add_timeline_event",
    "get_timeline_events",
    "delete_timeline_events",
    "save_memory",
    "get_memory",
    "load_all_memory",
    "save_chat_message",
    "get_chat_history",
]
