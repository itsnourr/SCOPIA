"""
Memory Extraction Module for Forensic Chatbot

Extracts user personal information from messages to store in long-term memory.
Uses regex patterns for common cases, with LLM fallback for general extraction.

IMPORTANT: Only extracts user personal preferences/info, NOT case evidence or suspect details.
"""

import re
import logging
from typing import List, Tuple, Optional

from app.llm_factory import create_llm
from config import Config


logger = logging.getLogger(__name__)


def extract_memory(user_message: str) -> List[Tuple[str, str]]:
    """
    Extract memory key-value pairs from user message
    
    Detects statements like:
    - "my name is X" → ("name", "X")
    - "call me X" → ("name", "X")
    - "I live in X" → ("location", "X")
    - "my birthday is X" → ("birthday", "X")
    - "my car is a X" → ("car", "X")
    - "my job is X" → ("job", "X")
    
    Uses regex patterns first, then falls back to LLM extraction if no matches found.
    
    Args:
        user_message: User's message text
        
    Returns:
        List of tuples (key, value) representing extracted memories
        
    Example:
        >>> extract_memory("my name is Sami")
        [("name", "Sami")]
        
        >>> extract_memory("I live in Beirut and my birthday is May 2")
        [("location", "Beirut"), ("birthday", "May 2")]
    """
    if not user_message or not user_message.strip():
        return []
    

    regex_memories = _extract_with_regex(user_message)
    
    if regex_memories:
        logger.info(f"✅ Extracted {len(regex_memories)} memory items using regex")
        return regex_memories
    

    llm_memories = _extract_with_llm(user_message)
    
    if llm_memories:
        logger.info(f"✅ Extracted {len(llm_memories)} memory items using LLM")
        return llm_memories
    
    return []


def _extract_with_regex(message: str) -> List[Tuple[str, str]]:
    """
    Extract memory using regex patterns (priority method)
    
    Patterns are designed to catch common personal information statements.
    Returns empty list if no matches found.
    """
    memories = []
    message_lower = message.lower().strip()
    

    name_patterns = [
        (r'\bmy name is\s+([A-Za-z\s]+?)(?:\.|,|\s+and|\s+$)', 'name'),
        (r'\bcall me\s+([A-Za-z\s]+?)(?:\.|,|\s+and|\s+$)', 'name'),
        (r'\bi\'?m\s+([A-Za-z\s]+?)(?:\.|,|\s+and|\s+$)', 'name'),
        (r'\bi am\s+([A-Za-z\s]+?)(?:\.|,|\s+and|\s+$)', 'name'),
    ]
    
    for pattern, key in name_patterns:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            value = match.group(1).strip()

            value = re.sub(r'\s+(and|or|but|the|a|an)\s*$', '', value, flags=re.IGNORECASE)
            if value and len(value) > 0:
                memories.append((key, value))
                break
    

    location_patterns = [
        (r'\bi live in\s+([A-Za-z\s]+?)(?:\s*,\s*(?:my\s+(?:birthday|name|job|car|location)|i\s+(?:was|am))|\s*\.|\s*$)', 'location'),
        (r'\bmy location is\s+([A-Za-z\s]+?)(?:\s*,\s*(?:my\s+(?:birthday|name|job|car|location)|i\s+(?:was|am))|\s*\.|\s*$)', 'location'),
        (r'\bi\'?m from\s+([A-Za-z\s]+?)(?:\s*,\s*(?:my\s+(?:birthday|name|job|car|location)|i\s+(?:was|am))|\s*\.|\s*$)', 'location'),
        (r'\bi\'?m located in\s+([A-Za-z\s]+?)(?:\s*,\s*(?:my\s+(?:birthday|name|job|car|location)|i\s+(?:was|am))|\s*\.|\s*$)', 'location'),
    ]
    
    for pattern, key in location_patterns:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            value = match.group(1).strip()

            value = re.sub(r'\s+(and|or|but|the|a|an)\s*$', '', value, flags=re.IGNORECASE)
            if value and len(value) > 0:
                memories.append((key, value))
                break
    

    birthday_patterns = [
        (r'\bmy birthday is\s+(?:on\s+)?([A-Za-z0-9\s,]+?)(?:\.|,|\s+and|\s+$)', 'birthday'),
        (r'\bmy birth date is\s+(?:on\s+)?([A-Za-z0-9\s,]+?)(?:\.|,|\s+and|\s+$)', 'birthday'),
        (r'\bi was born on\s+([A-Za-z0-9\s,]+?)(?:\.|,|\s+and|\s+$)', 'birthday'),
        (r'\bmy birthday\s+(?:is\s+)?(?:on\s+)?([A-Za-z0-9\s,]+?)(?:\.|,|\s+and|\s+$)', 'birthday'),
    ]
    
    for pattern, key in birthday_patterns:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            value = match.group(1).strip()

            value = re.sub(r'\s+(and|or|but|the|a|an)\s*$', '', value, flags=re.IGNORECASE)
            if value and len(value) > 0:
                memories.append((key, value))
                break
    

    car_patterns = [
        (r'\bmy car is\s+(?:a\s+)?([A-Za-z0-9\s,]+?)(?:\.|,|\s+and|\s+$)', 'car'),
        (r'\bmy vehicle is\s+(?:a\s+)?([A-Za-z0-9\s,]+?)(?:\.|,|\s+and|\s+$)', 'car'),
        (r'\bi drive\s+(?:a\s+)?([A-Za-z0-9\s,]+?)(?:\.|,|\s+and|\s+$)', 'car'),
    ]
    
    for pattern, key in car_patterns:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            value = re.sub(r'\s+(and|or|but|the|a|an)\s*$', '', value, flags=re.IGNORECASE)
            if value and len(value) > 0:
                memories.append((key, value))
                break
    

    job_patterns = [
        (r'\bmy job is\s+(?:a\s+)?([A-Za-z\s]+?)(?:\.|,|\s+and|\s+$)', 'job'),
        (r'\bi work as\s+(?:a\s+)?([A-Za-z\s]+?)(?:\.|,|\s+and|\s+$)', 'job'),
        (r'\bi\'?m a\s+([A-Za-z\s]+?)(?:\.|,|\s+and|\s+$)', 'job'),
        (r'\bmy occupation is\s+(?:a\s+)?([A-Za-z\s]+?)(?:\.|,|\s+and|\s+$)', 'job'),
    ]
    
    for pattern, key in job_patterns:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            value = re.sub(r'\s+(and|or|but|the|a|an)\s*$', '', value, flags=re.IGNORECASE)
            if value and len(value) > 0:
                memories.append((key, value))
                break
    

    email_patterns = [
        (r'\bmy email is\s+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', 'email'),
        (r'\bmy e-mail is\s+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', 'email'),
    ]
    
    for pattern, key in email_patterns:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value:
                memories.append((key, value))
                break
    
    return memories


def _extract_with_llm(message: str) -> List[Tuple[str, str]]:
    """
    Extract memory using LLM (Gemini Flash, temperature 0.0 for determinism)
    
    This is a fallback when regex patterns don't match.
    Only extracts user personal information, NOT case evidence.
    """
    if not Config.GEMINI_API_KEY and not Config.OPENAI_API_KEY:
        logger.warning("⚠️ No API key configured - skipping LLM extraction")
        return []
    
    try:

        llm = create_llm(temperature=0.0)
        

        prompt = f"""Extract personal information from this user message. 
ONLY extract user personal details (name, location, birthday, preferences, etc.).
DO NOT extract any case evidence, suspect information, or crime-related details.

ETHICAL USE & RESPONSIBILITY:
- This system is for legitimate law enforcement and forensic investigation purposes only
- Only extract information explicitly provided by the user for personalization
- Do not infer or assume personal information not stated
- Respect user privacy - only store what the user explicitly shares
- Maintain professional standards and ethical conduct at all times

User message: "{message}"

If you find any personal information, return it in this exact format (one per line):
KEY: VALUE

Examples:
name: Sami
location: Beirut
birthday: May 2
car: red Honda
job: engineer

If no personal information is found, return only: NONE

Return only the key-value pairs or NONE, nothing else:"""
        
        response = llm.invoke(prompt)
        response_text = response.content.strip()
        
        if not response_text or response_text.upper() == "NONE":
            return []
        

        memories = []
        for line in response_text.split('\n'):
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    if key and value:
                        memories.append((key, value))
        
        return memories
        
    except Exception as e:
        logger.error(f"❌ Error in LLM memory extraction: {e}")
        return []


def is_memory_question(user_message: str) -> Optional[str]:
    """
    Detect if user is asking about stored memory
    
    Args:
        user_message: User's question
        
    Returns:
        Memory key if question is about memory (e.g., "name", "location"), None otherwise
        
    Example:
        >>> is_memory_question("What is my name?")
        "name"
        
        >>> is_memory_question("Do you remember my birthday?")
        "birthday"
        
        >>> is_memory_question("What car do I drive?")
        "car"
    """
    message_lower = user_message.lower().strip()
    

    memory_patterns = [
        (r'\bwhat (?:is|was) my (?:name|full name)\??', 'name'),
        (r'\bdo you (?:remember|know) my name\??', 'name'),
        (r'\bwhat did i tell you (?:my name is|about my name)\??', 'name'),
        (r'\bwhat (?:is|was) my (?:location|city|address)\??', 'location'),
        (r'\bwhere (?:do|did) i (?:live|reside)\??', 'location'),
        (r'\bdo you (?:remember|know) where i live\??', 'location'),
        (r'\bwhat (?:is|was) my (?:birthday|birth date)\??', 'birthday'),
        (r'\bdo you (?:remember|know) my birthday\??', 'birthday'),
        (r'\bwhen (?:is|was) my birthday\??', 'birthday'),
        (r'\bwhat (?:car|vehicle) (?:do|did) i (?:drive|own|have)\??', 'car'),
        (r'\bdo you (?:remember|know) (?:what car|my car)\??', 'car'),
        (r'\bwhat (?:is|was) my (?:job|occupation|profession)\??', 'job'),
        (r'\bdo you (?:remember|know) (?:what i do|my job)\??', 'job'),
        (r'\bwhat did i tell you (?:before|earlier|previously)\??', ''),
    ]
    
    for pattern, key in memory_patterns:
        if re.search(pattern, message_lower, re.IGNORECASE):
            return key
    
    return None

