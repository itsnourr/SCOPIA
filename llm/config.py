"""
Configuration management for Forensic Crime Analysis Agent
Loads environment variables and provides typed configuration objects
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    PROJECT_ROOT: Path = Path(__file__).parent
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://forensic_user:password@localhost:5432/forensic_db"
    )
    
    AES_MASTER_KEY: str = os.getenv("AES_MASTER_KEY", "")
    
    FILES_DIR: Path = Path(os.getenv("FILES_DIR", "./data/encrypted"))
    CHROMA_DIR: Path = Path(os.getenv("CHROMA_DIR", "./data/chroma"))
    
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    
    MIN_CONFIDENCE_THRESHOLD: float = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.65"))
    ENABLE_ETHICAL_GUARDRAILS: bool = os.getenv("ENABLE_ETHICAL_GUARDRAILS", "true").lower() == "true"
    
    LANGCHAIN_VERBOSE: bool = os.getenv("LANGCHAIN_VERBOSE", "false").lower() == "true"
    LANGCHAIN_TEMPERATURE: float = float(os.getenv("LANGCHAIN_TEMPERATURE", "0.1"))
    
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "forensic_evidence")
    
    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate required configuration values
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not cls.GEMINI_API_KEY and not cls.OPENAI_API_KEY:
            errors.append("Either GEMINI_API_KEY or OPENAI_API_KEY is required")
        
        if not cls.AES_MASTER_KEY:
            errors.append("AES_MASTER_KEY is required (generate with: python -c \"import secrets; print(secrets.token_hex(32))\")")
        elif len(cls.AES_MASTER_KEY) != 64:
            errors.append("AES_MASTER_KEY must be 64 hexadecimal characters (32 bytes)")
        
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        
        return errors
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist"""
        cls.FILES_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        
        logs_dir = cls.PROJECT_ROOT / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)


config = Config()


def get_config() -> Config:
    """Get configuration instance"""
    return config


if __name__ == "__main__":
    print("Validating configuration...")
    errors = Config.validate()
    
    if errors:
        print("\n❌ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        exit(1)
    else:
        print("✅ Configuration is valid!")
        print(f"\n📁 Files directory: {Config.FILES_DIR}")
        print(f"📁 Chroma directory: {Config.CHROMA_DIR}")
        print(f"🗃️  Database: {Config.DATABASE_URL.split('@')[-1]}")
        print(f"🔐 Encryption key: {'*' * 20} (configured)")
        Config.ensure_directories()
        print("\n✅ All directories created successfully!")

