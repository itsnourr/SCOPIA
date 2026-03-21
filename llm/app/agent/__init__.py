"""
Forensic Agent Module

Provides LangChain-based agent powered by Gemini Pro for:
- Evidence retrieval via RAG
- Suspect ranking with transparent reasoning
- General Q&A
- Safety guardrails and insufficient evidence handling

Main Entry Points:
    - answer_question(): Router for all queries
    - answer_general(): General Q&A
    - answer_rank_suspects(): Suspect correlation and ranking
    - detect_intent(): Query intent classification

Example:
    >>> from app.agent import answer_question
    >>> 
    >>> result = answer_question(case_id=1, user_query="Who is the most likely suspect?")
    >>> print(result['answer'])
    >>> 
    >>> if 'ranked' in result:
    ...     for suspect in result['ranked']:
    ...         print(f"{suspect['suspect_name']}: {suspect['score']:.2f}")
"""

from app.agent.forensic_agent import (

    answer_question,
    answer_general,
    answer_rank_suspects,
    

    detect_intent,
    to_markdown,
    build_llm,
    

    SYSTEM_PROMPT
)
from app.agent.utils import format_context


from app.agent.tools import get_case_summary, analyze_timeline_text
from app.agent.langchain_agent import create_tool_enabled_agent, answer_with_tools

__all__ = [

    "answer_question",
    "answer_general",
    "answer_rank_suspects",
    

    "detect_intent",
    "format_context",
    "to_markdown",
    "build_llm",
    

    "SYSTEM_PROMPT",
    

    "get_case_summary",
    "analyze_timeline_text",
    "create_tool_enabled_agent",
    "answer_with_tools",
]
