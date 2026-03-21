"""
LLM Factory - Unified interface for multiple LLM providers

Supports:
- Google Gemini (via langchain_google_genai)
- OpenAI (via langchain_openai)

Automatically selects provider based on configuration.
"""

import logging
from typing import Union, Optional, Any
from langchain_core.language_models import BaseChatModel

from config import Config

logger = logging.getLogger(__name__)


def create_llm(
    temperature: float = 0.2,
    model: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """
    Create LLM instance from configured provider
    
    Priority:
    1. If OPENAI_API_KEY is set → Use OpenAI
    2. If GEMINI_API_KEY is set → Use Gemini
    3. Otherwise → Raise error
    
    Args:
        temperature: Sampling temperature [0, 1]
        model: Model name (optional, uses provider default)
        **kwargs: Additional parameters for LLM
        
    Returns:
        Configured LLM instance (ChatOpenAI or ChatGoogleGenerativeAI)
        
    Example:
        >>> llm = create_llm(temperature=0.1)
        >>> response = llm.invoke("Hello")
    """
    if Config.OPENAI_API_KEY:
        return _create_openai_llm(temperature, model, **kwargs)
    elif Config.GEMINI_API_KEY:
        return _create_gemini_llm(temperature, model, **kwargs)
    else:
        raise ValueError(
            "No LLM API key configured. "
            "Set either OPENAI_API_KEY or GEMINI_API_KEY in .env"
        )


def _create_openai_llm(
    temperature: float = 0.2,
    model: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """Create OpenAI LLM instance"""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai not installed. "
            "Install with: pip install langchain-openai"
        )
    
    model_name = model or Config.OPENAI_MODEL or "gpt-4o-mini"
    
    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=Config.OPENAI_API_KEY,
        temperature=temperature,
        **kwargs
    )
    
    logger.info(f"✅ Created OpenAI LLM (model={model_name}, temperature={temperature})")
    return llm


def _create_gemini_llm(
    temperature: float = 0.2,
    model: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """Create Gemini LLM instance"""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ImportError(
            "langchain-google-genai not installed. "
            "Install with: pip install langchain-google-genai"
        )
    
    model_name = model or Config.GEMINI_MODEL or "gemini-1.5-flash"
    
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=Config.GEMINI_API_KEY,
        temperature=temperature,
        convert_system_message_to_human=True,
        **kwargs
    )
    
    logger.info(f"✅ Created Gemini LLM (model={model_name}, temperature={temperature})")
    return llm

