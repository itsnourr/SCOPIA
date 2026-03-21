"""
Database initialization script for Forensic Crime Analysis Agent
Creates all tables and manages database schema
"""

import sys
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import sessionmaker


project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from app.db.models import Base, Case, Suspect, TextDocument, Image, AnalysisResult, PolarityCache, TimelineEvent, ChatMemory, ChatHistory


logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connection(engine) -> bool:
    """
    Test if database connection is working
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return False


def init_db(drop_existing: bool = False) -> bool:
    """
    Initialize database schema by creating all tables
    
    Args:
        drop_existing: If True, drop all existing tables before creating (DANGEROUS!)
        
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        logger.info("Starting database initialization...")
        logger.info(f"Database URL: {Config.DATABASE_URL.split('@')[-1]}")
        

        engine = create_engine(
            Config.DATABASE_URL,
            echo=Config.LOG_LEVEL == "DEBUG",
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        

        if not test_connection(engine):
            logger.error("❌ Cannot connect to database. Check DATABASE_URL in .env")
            return False
        
        logger.info("✅ Database connection successful")
        

        if drop_existing:
            logger.warning("⚠️  Dropping all existing tables...")
            Base.metadata.drop_all(engine)
            logger.info("✅ Existing tables dropped")
        

        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        

        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result]
            
        expected_tables = [
            'cases', 'suspects', 'text_documents', 'images', 'analysis_results', 
            'polarity_cache', 'timeline_events', 'chat_memory', 'chat_history'
        ]
        
        created_tables = [t for t in expected_tables if t in tables]
        
        logger.info(f"✅ Database initialization complete!")
        logger.info(f"✅ Created {len(created_tables)} tables:")
        for table in created_tables:
            logger.info(f"   - {table}")
        

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        

        with SessionLocal() as session:
            count = session.query(Case).count()
            logger.info(f"✅ Database query test passed (found {count} cases)")
        
        return True
        
    except OperationalError as e:
        logger.error(f"❌ Database operational error: {e}")
        logger.error("Check that PostgreSQL is running and DATABASE_URL is correct")
        return False
    except ProgrammingError as e:
        logger.error(f"❌ Database programming error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during database initialization: {e}")
        logger.exception(e)
        return False


def reset_db() -> bool:
    """
    Reset database by dropping and recreating all tables
    ⚠️  WARNING: This will delete ALL data!
    
    Returns:
        True if reset successful, False otherwise
    """
    logger.warning("=" * 60)
    logger.warning("⚠️  DATABASE RESET REQUESTED - ALL DATA WILL BE DELETED!")
    logger.warning("=" * 60)
    
    return init_db(drop_existing=True)


def get_engine():
    """
    Get SQLAlchemy engine instance
    
    Returns:
        SQLAlchemy Engine
    """
    return create_engine(
        Config.DATABASE_URL,
        echo=Config.LOG_LEVEL == "DEBUG",
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )


def get_session_factory():
    """
    Get session factory for creating database sessions
    
    Returns:
        SQLAlchemy sessionmaker
    """
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


if __name__ == "__main__":
    """
    Command-line interface for database initialization
    
    Usage:
        python -m app.db.init_db           # Initialize database
        python -m app.db.init_db --reset   # Reset database (drops all data)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize forensic analysis database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (WARNING: deletes all data)"
    )
    
    args = parser.parse_args()
    

    config_errors = Config.validate()
    if config_errors:
        logger.error("❌ Configuration errors found:")
        for error in config_errors:
            logger.error(f"   - {error}")
        sys.exit(1)
    

    if args.reset:
        success = reset_db()
    else:
        success = init_db()
    

    sys.exit(0 if success else 1)

