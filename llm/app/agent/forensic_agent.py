"""
Forensic Analysis Agent powered by Gemini 2.5 Flash

This agent integrates:
- RAG for evidence retrieval
- Custom tools (Evidence Correlator)
- Gemini 2.5 Flash LLM for reasoning
- Safety guardrails
- Two-mode answering system

The agent can:
- Answer simple factual questions (1-2 sentences) - "How did the victim die?"
- Answer complex questions with full forensic analysis - "Summarize all evidence"
- Rank suspects with transparent reasoning
- Detect insufficient evidence and refuse to speculate

Example Usage:
    >>> from app.agent.forensic_agent import answer_question
    >>> 
    >>> # Ask a question
    >>> result = answer_question(case_id=1, user_query="Who is the most likely suspect and why?")
    >>> print(result["answer"])
    >>> 
    >>> # Check if suspects were ranked
    >>> if 'ranked' in result:
    ...     for suspect in result['ranked']:
    ...         print(f"{suspect['suspect_name']}: {suspect['score']:.2f}")
    
Integration Hook (Streamlit):
    ```python
    import streamlit as st
    from app.agent.forensic_agent import answer_question, to_markdown
    
    # User submits query
    query = st.text_input("Ask about the case:")
    if st.button("Analyze"):
        result = answer_question(case_id=current_case_id, user_query=query)
        
        # Display formatted answer
        st.markdown(to_markdown(result))
        
        # If suspects ranked, show bar chart
        if 'ranked' in result and result['ranked']:
            scores = {s['suspect_name']: s['score'] for s in result['ranked']}
            st.bar_chart(scores)
    ```
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

try:
    from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
except ImportError:

    from langchain.schema import HumanMessage, AIMessage, BaseMessage

from config import Config
from app.llm_factory import create_llm
from app.rag import query_documents, get_case_index_status
from app.tools.evidence_correlator import (
    extract_evidence_context,
    score_suspects,
    correlate_and_persist
)
from app.db import get_case, get_suspects_by_case
from app.db.dao import save_memory, get_memory, load_all_memory, save_chat_message, get_chat_history
from app.tools.memory_extractor import extract_memory, is_memory_question
from app.agent.tools import get_case_summary, analyze_timeline_text
from app.agent.tool_runner import run_tool
from app.agent.utils import format_context
import inspect


logger = logging.getLogger(__name__)





ETHICAL_GUIDELINES = """
ETHICAL USE & RESPONSIBILITY:
- This system is for legitimate law enforcement and forensic investigation purposes only
- Never use this system to fabricate, manipulate, or misrepresent evidence
- All analysis is decision support only, not a legal conclusion
- Respect presumption of innocence - never conclude guilt definitively
- Acknowledge limitations and gaps in evidence
- Distinguish correlation from causation
- Flag when evidence is circumstantial
- Do not use this system to target individuals based on protected characteristics
- Maintain professional standards and ethical conduct at all times
- Report any misuse or ethical concerns immediately
"""





SYSTEM_PROMPT = """You are a forensic analysis assistant for law enforcement investigators.

CRITICAL RULES:
1. Use ONLY the provided evidence from the RAG vector retriever (semantic search) and internal tools
2. The EVIDENCE CONTEXT section contains documents retrieved via RAG (Retrieval-Augmented Generation) - this is your PRIMARY source
3. Do NOT invent facts or speculate beyond the evidence
4. If evidence is insufficient, explicitly say: "Insufficient evidence" and list what's missing
5. ALWAYS cite document IDs/titles when making claims from RAG evidence (e.g., "According to [T1: Witness A]...")
6. DO NOT attempt to call tools or generate tool code - you are a text-only assistant that answers based on provided evidence
7. DO NOT output code blocks, tool calls, or function calls - just provide natural language answers

MANDATORY INCLUSIONS - You MUST include these critical details when present in evidence:
- **Fingerprint Analysis**: Always mention MATCH results, especially fingerprints on weapons (e.g., "MATCH to John Doe on knife handle")
- **Timeline Information**: Include specific timestamps from CCTV, witness statements, and forensic reports
- **Murder Window**: If multiple time windows are provided, use the MORE PRECISE one (CCTV/911 calls) as primary. Format: "Murder window: 10:15-10:35 PM (CCTV + 911 call)" with broader forensic window as secondary if different
- **Vehicle Timestamps**: Include arrival/departure times for vehicles matching suspect descriptions. ALSO include NEGATIVE evidence (e.g., "Blue truck (Jane Smith's) NOT present after 8:35 PM")
- **CCTV Conclusions**: Include conclusion statements from security camera analysis (e.g., "John Doe was inside building during murder window")
- **Presence During Crime**: Explicitly state if a suspect was present/absent during the murder window
- **Negative Evidence**: Include absence statements (e.g., "Vehicle NOT present after X time", "Suspect NOT seen in building")
- **Image Relevance**: If an image contains no crime-related objects, state: "No crime-related objects detected in the image"

When ranking suspects or answering "who committed" questions:
- Provide STRONG, DETAILED forensic analysis - do NOT just give a weak legal disclaimer
- Clearly identify which suspect has the STRONGEST evidence support
- Show deductive reasoning: explain WHY the evidence points to each suspect
- Contrast suspects: compare evidence strength across all suspects
- Articulate probability and reasoning: explain the weight of evidence
- Maintain legal neutrality: state "strongest evidence points to X" rather than "X is guilty"
- Use phrases like: "The evidence most strongly supports...", "The preponderance of evidence indicates...", "Based on forensic analysis, X has the strongest correlation..."
- DO NOT just say "we cannot definitively conclude" without providing the analysis
- Include this caveat at the END: "This analysis is decision support only, not a legal conclusion"
- DO NOT try to manually call tools or generate tool code

STYLE:
- Concise, professional tone
- Use bullet points and numbered reasoning
- Separate facts from inferences
- Highlight confidence levels (high/medium/low)
- Organize by category: Forensic Findings, Witness Statements, CCTV Analysis, Suspect Profiles, Image Evidence

ETHICAL GUARDRAILS:
- Never conclude guilt definitively
- Acknowledge limitations and gaps in evidence
- Distinguish correlation from causation
- Respect presumption of innocence
- Flag when evidence is circumstantial

Remember: Your role is to assist human investigators, not replace their judgment.

{ETHICAL_GUIDELINES}""".format(ETHICAL_GUIDELINES=ETHICAL_GUIDELINES)





def build_llm(temperature: float = 0.2, **kwargs):
    """
    Build LLM client with sensible defaults (supports OpenAI or Gemini)
    
    Args:
        temperature: Sampling temperature [0, 1] (0.2 for more deterministic)
        **kwargs: Additional parameters for LLM
        
    Returns:
        Configured LLM client (OpenAI or Gemini)
        
    Example:
        >>> llm = build_llm(temperature=0.1)
        >>> response = llm.invoke("What is forensic analysis?")
    """
    return create_llm(temperature=temperature, **kwargs)






class ForensicLLM:
    """
    LLM wrapper class with internal message history (supports OpenAI or Gemini)
    
    This class provides:
    - Internal message history management
    - Clean send_message() method
    - Temperature and model configuration
    - Reusable architecture
    
    Example:
        >>> llm = ForensicLLM(temperature=0.2)
        >>> response = llm.send_message("What is forensic analysis?")
        >>> print(response)
    """
    
    def __init__(self, temperature: float = 0.2, model: Optional[str] = None, **kwargs):
        """
        Initialize ForensicLLM wrapper
        
        Args:
            temperature: Sampling temperature [0, 1] (0.2 for more deterministic)
            model: Model name (optional, uses provider default)
            **kwargs: Additional parameters for LLM
        """
        self.temperature = temperature
        self.model = model
        self.llm = create_llm(temperature=temperature, model=model, **kwargs)
        
        if hasattr(self.llm, 'model_name'):
            self.model = self.model or self.llm.model_name
        elif hasattr(self.llm, 'model'):
            self.model = self.model or self.llm.model

        self.message_history: List[BaseMessage] = []
        
        logger.info(f"✅ Initialized ForensicLLM (model={self.model}, temperature={temperature})")
    
    def send_message(self, message: str, system_prompt: Optional[str] = None) -> str:
        """
        Send a message to the LLM and get a response.
        
        This method:
        1. Adds the user message to internal history as HumanMessage
        2. Invokes the LLM with the full message history
        3. Adds the AI response to history as AIMessage
        4. Returns the response text
        
        Args:
            message: User message text
            system_prompt: Optional system prompt (added as first message if provided)
            
        Returns:
            AI response text
            
        Example:
            >>> llm = ForensicLLM()
            >>> response = llm.send_message("What is forensic analysis?")
            >>> print(response)
        """

        messages: List[BaseMessage] = []
        

        if system_prompt:

            messages.append(HumanMessage(content=system_prompt))
        

        messages.extend(self.message_history)
        

        user_msg = HumanMessage(content=message)
        messages.append(user_msg)
        

        try:
            response = self.llm.invoke(messages)
            

            if hasattr(response, 'content'):
                response_text = response.content.strip()
            else:
                response_text = str(response).strip()
            

            self.message_history.append(user_msg)
            self.message_history.append(AIMessage(content=response_text))
            
            logger.debug(f"✅ LLM response generated ({len(response_text)} chars)")
            return response_text
            
        except Exception as e:
            logger.error(f"Error in LLM invocation: {e}")
            raise
    
    def clear_history(self):
        """Clear internal message history"""
        self.message_history = []
        logger.debug("Cleared message history")
    
    def get_history(self) -> List[BaseMessage]:
        """Get current message history"""
        return self.message_history.copy()






def detect_intent(user_query: str) -> Dict[str, Any]:
    """
    Detect user intent from query using keyword heuristics
    
    Args:
        user_query: User's question
        
    Returns:
        Dictionary with:
            - intent: 'rank_suspects' | 'general_qa' | 'summarize' | 'timeline' | 'unknown'
            - confidence: float [0, 1]
            
    Example:
        >>> detect_intent("Who is the most likely suspect?")
        {'intent': 'rank_suspects', 'confidence': 0.9}
        
        >>> detect_intent("Summarize the evidence")
        {'intent': 'summarize', 'confidence': 0.8}
    """
    query_lower = user_query.lower()
    

    rank_patterns = [
        r'\b(who|which)\b.*\b(suspect|guilty|responsible|culprit|perpetrator)\b',
        r'\bmost likely\b.*\b(suspect|person)\b',
        r'\brank\b.*\bsuspect',
        r'\bsuspect.*\brank',
        r'\bwho did (it|this)',
        r'\bwho commit',
        r'\bwho.*definitely\b',
        r'\bdefinitely.*(commit|murder|kill)',
        r'\bprime suspect',
        r'\bmain suspect',
        r'\btop suspect',
        r'\bleading suspect'
    ]
    
    for pattern in rank_patterns:
        if re.search(pattern, query_lower):
            return {'intent': 'rank_suspects', 'confidence': 0.9}
    

    summarize_patterns = [
        r'\bsummari[zs]e\b',
        r'\boverview\b',
        r'\bwhat happened\b',
        r'\bwhat do we know\b',
        r'\bgive me (a|an)?\s*(summary|overview)',
        r'\bkey points\b',
        r'\bmain points\b'
    ]
    
    for pattern in summarize_patterns:
        if re.search(pattern, query_lower):
            return {'intent': 'summarize', 'confidence': 0.8}
    

    timeline_patterns = [
        r'\btimeline\b',
        r'\bchronolog',
        r'\bsequence of events\b',
        r'\bwhen did\b',
        r'\bwhat time\b',
        r'\border of events\b'
    ]
    
    for pattern in timeline_patterns:
        if re.search(pattern, query_lower):
            return {'intent': 'timeline', 'confidence': 0.8}
    

    return {'intent': 'general_qa', 'confidence': 0.5}






def is_simple_fact_query(query: str) -> bool:
    """
    Detect if a query is asking for a simple factual answer (1-2 sentences)
    vs. a full forensic analysis.
    
    Args:
        query: User's question
        
    Returns:
        True if query is a simple fact question, False otherwise
        
    Example:
        >>> is_simple_fact_query("How did the victim die?")
        True
        >>> is_simple_fact_query("Summarize all evidence")
        False
    """
    query_lower = query.lower().strip()
    
    SIMPLE_PATTERNS = [
        "how did", "what caused", "cause of death",
        "what time", "when did", "what weapon",
        "who died", "who was killed", "time of death",
        "where was", "what is", "what was",
        "when was the murder", "how many wounds",
        "what killed", "how many", "what color",
        "what type", "what model", "what make",
        "who found", "who discovered", "who reported"
    ]
    

    if any(pattern in query_lower for pattern in SIMPLE_PATTERNS):

        EXCLUDE_PATTERNS = [
            "summarize", "explain everything", "full analysis",
            "complete", "all evidence", "detailed"
        ]
        if not any(exclude in query_lower for exclude in EXCLUDE_PATTERNS):
            return True
    
    return False






def detect_and_use_tools(case_id: int, query: str) -> Tuple[List[str], str, List[Dict[str, Any]]]:
    """
    Detect if tools should be used based on query and call them.
    
    Args:
        case_id: Case ID
        query: User query
        
    Returns:
        Tuple of (list of tool names used, tool results string, list of tool_result dicts)
    """
    tools_used = []
    tool_results = []
    tool_result_objects = []
    query_lower = query.lower()
    

    summary_keywords = ['summary', 'overview', 'case info', 'what is the case', 'tell me about the case', 
                       'case details', 'case summary', 'summarize this case', 'summarize the case', 
                       'summarize case', 'give me a summary', 'case overview']
    if any(keyword in query_lower for keyword in summary_keywords):
        logger.info(f"🔍 Detected case summary request in query: {query}")
        try:
            tool_result = run_tool(
                "get_case_summary",
                get_case_summary,
                {"case_id": case_id}
            )
            tools_used.append('get_case_summary')
            tool_result_objects.append(tool_result)
            tool_results.append(f"=== Case Summary (from get_case_summary tool) ===\n{tool_result['output']}\n")
        except Exception as e:
            logger.error(f"Error calling get_case_summary: {e}")
    

    timeline_keywords = ['extract timeline', 'analyze timeline', 'timeline events', 'extract events', 'what happened when', 
                        'what is the timeline', 'show timeline', 'timeline of events', 'sequence of events', 'chronology']
    if any(keyword in query_lower for keyword in timeline_keywords):

        text_to_analyze = query
        if ':' in query:

            text_to_analyze = query.split(':', 1)[1].strip()
        elif '"' in query:

            import re
            quoted = re.findall(r'"([^"]*)"', query)
            if quoted:
                text_to_analyze = quoted[0]
        
        if text_to_analyze and len(text_to_analyze) > 20:
            try:
                tool_result = run_tool(
                    "analyze_timeline_text",
                    analyze_timeline_text,
                    {
                        'text': text_to_analyze,
                        'case_id': case_id
                    }
                )
                tools_used.append('analyze_timeline_text')
                tool_result_objects.append(tool_result)
                tool_results.append(f"=== Timeline Analysis (from analyze_timeline_text tool) ===\n{tool_result['output']}\n")
            except Exception as e:
                logger.error(f"Error calling analyze_timeline_text: {e}")
    
    tool_results_str = "\n".join(tool_results) if tool_results else ""
    return tools_used, tool_results_str, tool_result_objects


def get_tool_code(tool_name: str) -> str:
    """
    Get the source code of a tool function.
    
    Args:
        tool_name: Name of the tool ('get_case_summary' or 'analyze_timeline_text')
        
    Returns:
        Source code as string
    """

    import app.agent.tools as tools_module
    
    if tool_name == 'get_case_summary':
        try:


            import os
            tools_file = os.path.join(os.path.dirname(__file__), 'tools.py')
            with open(tools_file, 'r', encoding='utf-8') as f:
                content = f.read()

                import re
                pattern = r'@tool\("get_case_summary".*?def get_case_summary\(.*?\) -> str:.*?"""(?:.*?""")?.*?(?=\n@tool|\n\n\n|\Z)'
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    return match.group(0)

                start = content.find('def get_case_summary')
                if start != -1:

                    end = content.find('@tool', start + 1)
                    if end == -1:
                        end = content.find('\n\n\n', start)
                    if end == -1:
                        end = len(content)
                    return content[start:end].strip()
        except Exception as e:
            logger.error(f"Error getting source code for {tool_name}: {e}")
            return f"# Error retrieving source code: {e}\n# Tool: {tool_name}"
    
    elif tool_name == 'analyze_timeline_text':
        try:
            import os
            tools_file = os.path.join(os.path.dirname(__file__), 'tools.py')
            with open(tools_file, 'r', encoding='utf-8') as f:
                content = f.read()

                start = content.find('def analyze_timeline_text')
                if start != -1:

                    end = content.find('\n\n\n', start)
                    if end == -1:
                        end = len(content)
                    return content[start:end].strip()
        except Exception as e:
            logger.error(f"Error getting source code for {tool_name}: {e}")
            return f"# Error retrieving source code: {e}\n# Tool: {tool_name}"
    
    return f"# Tool '{tool_name}' not found"










def answer_simple_fact(
    case_id: int,
    query: str,
    k: Optional[int] = None,
    temperature: float = 0.2,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Answer simple factual questions with 1-2 sentence responses.
    
    This mode is for questions like:
    - "How did the victim die?"
    - "What is the murder weapon?"
    - "When was the murder?"
    
    Returns ONLY the answer, no extra details, suspects, or analysis.
    
    Args:
        case_id: Case ID
        query: User's simple question
        k: Number of documents to retrieve. If None, uses total indexed documents (capped at 30)
        temperature: LLM temperature
        
    Returns:
        Dictionary with:
            - answer: Short 1-2 sentence answer
            - context_used: True
            
    Example:
        >>> result = answer_simple_fact(case_id=1, query="How did the victim die?")
        >>> print(result['answer'])
        "The victim died from seven stab wounds inflicted with an 8-inch kitchen knife."
    """
    logger.info(f"📝 Simple fact query for case {case_id}: {query}")
    

    case = get_case(case_id)
    if not case:
        return {
            'answer': f"Error: Case {case_id} not found in database.",
            'context_used': False,
            'tools_used': []
        }
    

    if k is None:
        status = get_case_index_status(case_id)
        total_docs = status.get('document_count', 0)
        k = min(total_docs, 30) if total_docs > 0 else 6
        logger.info(f"📊 Using dynamic k={k} (total evidence: {total_docs})")
    

    docs = query_documents(query, case_id=case_id, k=k)
    
    if not docs:
        return {
            'answer': "Insufficient evidence: No relevant documents found to answer this question.",
            'context_used': False,
            'tools_used': []
        }
    

    evidence_texts = []
    for doc in docs:
        text = doc.get('text', '') or doc.get('page_content', '')
        evidence_texts.append(text[:500])
    

    evidence_context = "\n\n".join(evidence_texts)
    

    chat_history_block = ""
    if user_id:
        chat_history = get_chat_history(user_id, case_id=case_id, limit=10)
        if chat_history:
            chat_history.reverse()
            history_lines = []
            for msg in chat_history:
                role = "User" if msg.is_user else "Assistant"
                history_lines.append(f"{role}: {msg.message}")
            chat_history_block = "\n\nPrevious conversation:\n" + "\n".join(history_lines) + "\n"
    

    simple_system_prompt = f"""Answer the question concisely in 1-2 sentences ONLY.
{chat_history_block}

CRITICAL RULES:
- **PRIMARY SOURCE**: Use the "Relevant evidence" below (retrieved via RAG semantic search) as your PRIMARY source
- Do NOT include extra details, suspects, CCTV, timeline, or analysis
- Do NOT mention multiple pieces of evidence unless directly asked
- Answer ONLY what was asked
- Use the RAG-retrieved evidence below - chat history is only for personal questions
- If evidence is insufficient, say "Insufficient evidence"
- Cite evidence sources when possible (e.g., "According to [T1: Witness A]...")

{ETHICAL_GUIDELINES}

Relevant evidence (RAG-retrieved):
{evidence_context}"""
    
    try:

        llm_wrapper = ForensicLLM(temperature=temperature)
        answer = llm_wrapper.send_message(
            message=query,
            system_prompt=simple_system_prompt
        )
        

        sentences = answer.split('.')
        if len(sentences) > 2:

            answer = '. '.join(sentences[:2])
            if not answer.endswith('.'):
                answer += '.'
        
        logger.info(f"✅ Generated simple answer ({len(answer)} chars)")
        

        if user_id:
            save_chat_message(user_id, answer, False, case_id)
        
        return {
            'answer': answer,
            'context_used': True,
            'tools_used': []
        }
        
    except Exception as e:
        logger.error(f"Error generating simple answer: {e}")
        error_answer = f"Error: Failed to generate answer. {str(e)}"

        if user_id:
            save_chat_message(user_id, error_answer, False, case_id)
        return {
            'answer': error_answer,
            'context_used': False,
            'tools_used': []
        }






def answer_general(
    case_id: int,
    query: str,
    k: Optional[int] = None,
    temperature: float = 0.2,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Answer general questions using RAG + LLM
    
    Args:
        case_id: Case ID
        query: User's question
        k: Number of documents to retrieve. If None, uses total indexed documents for the case (capped at 30)
        temperature: LLM temperature
        
    Returns:
        Dictionary with:
            - answer: LLM response
            - context_used: Whether context was available
            
    Example:
        >>> result = answer_general(case_id=1, query="What vehicle was seen?")
        >>> print(result['answer'])
    """
    logger.info(f"🤔 Answering general question for case {case_id}: {query}")
    

    case = get_case(case_id)
    if not case:
        return {
            'answer': f"Error: Case {case_id} not found in database.",
            'context_used': False,
            'tools_used': []
        }
    

    status = get_case_index_status(case_id)
    if not status.get('indexed') or status.get('document_count', 0) == 0:
        return {
            'answer': "Insufficient evidence: This case has no indexed evidence. "
                     "Please add evidence documents and rebuild the case index before querying.",
            'context_used': False,
            'tools_used': []
        }
    



    try:
        from app.agent.langchain_agent import create_tool_enabled_agent, answer_with_tools
        
        logger.info("🔧 Using LangChain agent framework as primary execution engine (P3 compliance)")
        agent_result = answer_with_tools(case_id, query, user_id)
        

        if agent_result and agent_result.get('answer') and not agent_result.get('answer', '').startswith('Error'):
            logger.info("✅ Agent framework successfully processed query with automatic tool selection")

            tools_used = agent_result.get('tools_used', [])
            tool_result_objects = agent_result.get('tool_results', [])
            

            answer = agent_result.get('answer', '')
            

            if user_id:
                save_chat_message(user_id, answer, False, case_id)
            
            return {
                'answer': answer,
                'context_used': agent_result.get('context_used', True),
                'tools_used': tools_used if isinstance(tools_used, list) else (['agent_framework'] if tools_used else []),
                'tool_results': tool_result_objects
            }
    except Exception as e:
        logger.warning(f"⚠️ Agent framework failed, falling back to manual approach: {e}")

    


    if k is None:
        total_docs = status.get('document_count', 0)
        k = min(total_docs, 30) if total_docs > 0 else 10
        logger.info(f"📊 Fallback: Using dynamic k={k} (total evidence: {total_docs})")
    

    docs = query_documents(query=query, case_id=case_id, k=k)
    
    if not docs:
        return {
            'answer': "Insufficient evidence: No relevant documents found for this query. "
                     "The evidence may not contain information related to your question.",
            'context_used': False,
            'tools_used': []
        }
    

    context = format_context(docs)
    

    tools_used, tool_results, tool_result_objects = detect_and_use_tools(case_id, query)
    

    if tool_results:
        logger.info(f"🔧 Tools used: {tools_used}")


        escaped_tool_results = tool_results.replace('{', '{{').replace('}', '}}')
        tool_context = f"\n\n=== TOOL RESULTS (USE THIS AS PRIMARY SOURCE) ===\n{escaped_tool_results}\n"


        escaped_context = context.replace('{', '{{').replace('}', '}}') if context else ""
        context = f"Additional evidence context (use if tool results need more detail):\n{escaped_context}" if context else ""
    else:
        tool_context = ""
        tool_result_objects = []
    memory_block = ""
    chat_history_block = ""
    
    if user_id:

        memory = load_all_memory(user_id)
        if memory:
            memory_block = "\n".join([f"{k}: {v}" for k, v in memory.items()])
            memory_block = f"\n\nHere is what the user told you previously (long-term memory):\n{memory_block}\n"
        

        chat_history = get_chat_history(user_id, case_id=case_id, limit=20)
        if chat_history:

            chat_history.reverse()
            history_lines = []
            for msg in chat_history:
                role = "User" if msg.is_user else "Assistant"
                history_lines.append(f"{role}: {msg.message}")
            
            chat_history_block = "\n\nPrevious conversation history:\n" + "\n".join(history_lines) + "\n"
    


    if tool_results:
        primary_source_instruction = "**CRITICAL: PRIMARY SOURCE**: Use the TOOL RESULTS above as your PRIMARY and MAIN source. The tool results contain the exact, structured information requested. DO NOT use the evidence context below unless the tool results are incomplete."
        secondary_source_instruction = "**SECONDARY SOURCES**: Additional evidence context, chat history, and long-term memory are supplementary - only use if tool results need clarification."

        if 'get_case_summary' in tools_used:
            primary_source_instruction = "**CRITICAL: PRIMARY SOURCE**: Use the TOOL RESULTS above (from get_case_summary tool) as your PRIMARY and MAIN source. The tool provides comprehensive case information including suspects with profiles, evidence breakdown by type, key findings, timeline overview, and correlation results. Your task is to create a COMPLETE, ENHANCED summary that incorporates the tool's structured information but presents it in a natural, flowing narrative format. DO NOT simply repeat the tool output verbatim. Instead, synthesize the tool's information with specific evidence details from the context below to create a cohesive, comprehensive summary. Add specific citations, quotes, and details from the evidence context to make it more detailed and informative."
            secondary_source_instruction = "**SECONDARY SOURCES**: The evidence context below contains detailed evidence documents - use these to add specific details, citations, and examples to enhance the tool's summary. Chat history and long-term memory are supplementary."
    else:
        primary_source_instruction = "**PRIMARY SOURCE**: Use the EVIDENCE CONTEXT above (retrieved via semantic search/RAG) as your PRIMARY source for answering."
        secondary_source_instruction = "**SECONDARY SOURCES**: Chat history and long-term memory are supplementary - use them to provide context or personalize responses, but prioritize RAG evidence for factual answers."
    


    safe_memory_block = memory_block.replace('{', '{{').replace('}', '}}') if memory_block else ""
    safe_chat_history_block = chat_history_block.replace('{', '{{').replace('}', '}}') if chat_history_block else ""
    safe_context = context.replace('{', '{{').replace('}', '}}') if context else ""
    
    full_prompt = f"""{SYSTEM_PROMPT}{safe_memory_block}{safe_chat_history_block}

CASE: {case.title}

{tool_context}{safe_context}

USER QUESTION: {query}

Provide a clear, evidence-based answer.

IMPORTANT: 
- You are a text-only assistant. DO NOT attempt to call tools, generate code, or output function calls.
- {primary_source_instruction}
- {secondary_source_instruction}
- If the question is about case evidence, you MUST use the tool results (if provided) or RAG-retrieved evidence above.
- If the question is about personal information, check long-term memory first, then chat history.

CRITICAL REQUIREMENTS:
1. **Fingerprint Analysis**: If any document mentions fingerprint MATCH results (especially on weapons), you MUST include them with the exact match statement (e.g., "MATCH to John Doe on knife handle")
2. **Timeline Details**: Include ALL specific timestamps mentioned. If multiple time windows exist, use the MORE PRECISE one (CCTV/911 calls) as primary. Format: "Murder window: 10:15-10:35 PM (CCTV + 911 call)" with broader forensic estimate as secondary if different
3. **Vehicle Information**: Include BOTH positive (arrival/departure times) AND negative evidence (e.g., "Blue truck (Jane Smith's) NOT present after 8:35 PM")
4. **CCTV Conclusions**: Include any conclusion statements from security camera analysis
5. **Presence During Crime**: Explicitly state which suspects were present/absent during the murder window
6. **Negative Evidence**: Include absence statements (vehicles not present, suspects not seen) - these are important for establishing alibis
7. **All Witness Statements**: Mention ALL witness statements provided - do not skip any
8. **Image Relevance**: If an image contains no crime-related objects, explicitly state "No crime-related objects detected in the image"

Organize your response by category:
- === FORENSIC FINDINGS ===
- === WITNESS STATEMENTS ===
- === CCTV ANALYSIS ===
- === SUSPECT PROFILES ===
- === IMAGE EVIDENCE ===

{ETHICAL_GUIDELINES}""".format(ETHICAL_GUIDELINES=ETHICAL_GUIDELINES)
    
    try:

        llm_wrapper = ForensicLLM(temperature=temperature)
        

        system_prompt_text = SYSTEM_PROMPT + safe_memory_block + safe_chat_history_block + f"\n\nCASE: {case.title}\n\n{tool_context}{safe_context}\n\nUSER QUESTION: {query}\n\nProvide a clear, evidence-based answer.\n\nIMPORTANT: \n- You are a text-only assistant. DO NOT attempt to call tools, generate code, or output function calls.\n- {primary_source_instruction}\n- {secondary_source_instruction}\n- If the question is about case evidence, you MUST use the tool results (if provided) or RAG-retrieved evidence above.\n- If the question is about personal information, check long-term memory first, then chat history.\n\nCRITICAL REQUIREMENTS:\n1. **Fingerprint Analysis**: If any document mentions fingerprint MATCH results (especially on weapons), you MUST include them with the exact match statement (e.g., \"MATCH to John Doe on knife handle\")\n2. **Timeline Details**: Include ALL specific timestamps mentioned. If multiple time windows exist, use the MORE PRECISE one (CCTV/911 calls) as primary. Format: \"Murder window: 10:15-10:35 PM (CCTV + 911 call)\" with broader forensic estimate as secondary if different\n3. **Vehicle Information**: Include BOTH positive (arrival/departure times) AND negative evidence (e.g., \"Blue truck (Jane Smith's) NOT present after 8:35 PM\")\n4. **CCTV Conclusions**: Include any conclusion statements from security camera analysis\n5. **Presence During Crime**: Explicitly state which suspects were present/absent during the murder window\n6. **Negative Evidence**: Include absence statements (vehicles not present, suspects not seen) - these are important for establishing alibis\n7. **All Witness Statements**: Mention ALL witness statements provided - do not skip any\n8. **Image Relevance**: If an image contains no crime-related objects, explicitly state \"No crime-related objects detected in the image\"\n\nOrganize your response by category:\n- === FORENSIC FINDINGS ===\n- === WITNESS STATEMENTS ===\n- === CCTV ANALYSIS ===\n- === SUSPECT PROFILES ===\n- === IMAGE EVIDENCE ===\n\n{ETHICAL_GUIDELINES}".format(ETHICAL_GUIDELINES=ETHICAL_GUIDELINES)
        
        answer = llm_wrapper.send_message(
            message=query,
            system_prompt=system_prompt_text
        )
        
        logger.info(f"✅ Generated answer ({len(answer)} chars)")
        

        final_answer = answer
        if tool_result_objects:


            if 'get_case_summary' in tools_used:

                final_answer = answer
            else:

                tool_outputs_section = "\n\n=== TOOL OUTPUTS ===\n\n"
                for tool_result in tool_result_objects:

                    tool_outputs_section += "```\n" + tool_result['print_block'] + "\n```\n\n"
                
                tool_outputs_section += "=== AGENT RESPONSE ===\n\n"

                for tool_result in tool_result_objects:

                    tool_outputs_section += f"Tool {tool_result['tool']} returned:\n\n"
                    tool_outputs_section += str(tool_result['output']) + "\n\n"
                
                final_answer = tool_outputs_section + answer
        

        if user_id and tool_result_objects:
            for tool_result in tool_result_objects:

                save_chat_message(user_id, tool_result['print_block'], False, case_id)
        

        if user_id:
            save_chat_message(user_id, final_answer, False, case_id)
        
        return {
            'answer': final_answer,
            'context_used': True,
            'tools_used': tools_used,
            'tool_results': tool_result_objects
        }
        
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        error_answer = f"Error: Failed to generate answer. {str(e)}"

        if user_id:
            save_chat_message(user_id, error_answer, False, case_id)
        return {
            'answer': error_answer,
            'context_used': False,
            'tools_used': []
        }






def answer_rank_suspects(
    case_id: int,
    query: Optional[str] = None,
    k: Optional[int] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Rank suspects using Evidence Correlator with formatted output
    
    Args:
        case_id: Case ID
        query: Optional query (uses default if None)
        k: Number of documents to retrieve
        
    Returns:
        Dictionary with:
            - answer: Formatted ranking explanation
            - ranked: List of scored suspects
            - components: Analysis metadata
            
    Example:
        >>> result = answer_rank_suspects(case_id=1)
        >>> print(result['answer'])
        >>> for suspect in result['ranked']:
        ...     print(f"{suspect['suspect_name']}: {suspect['score']:.2f}")
    """
    logger.info(f"🎯 Ranking suspects for case {case_id}")
    

    case = get_case(case_id)
    if not case:
        return {
            'answer': f"Error: Case {case_id} not found in database.",
            'ranked': [],
            'components': {}
        }
    

    suspects = get_suspects_by_case(case_id)
    if not suspects:
        return {
            'answer': "Insufficient evidence: No suspects have been added to this case. "
                     "Please add suspect profiles before requesting a ranking.",
            'ranked': [],
            'components': {}
        }
    

    if k is None:
        status = get_case_index_status(case_id)
        total_docs = status.get('document_count', 0)
        k = min(total_docs, 30) if total_docs > 0 else 8
        logger.info(f"📊 Using dynamic k={k} (total evidence: {total_docs})")
    

    docs = extract_evidence_context(case_id, query, k)
    
    if not docs:
        return {
            'answer': "Insufficient evidence: No relevant evidence found in case database. "
                     "Please ensure evidence has been added and indexed before ranking suspects.",
            'ranked': [],
            'components': {'docs_used': 0}
        }
    

    ranked = score_suspects(case_id, docs)
    
    if not ranked or all(s['score'] == 0.0 for s in ranked):
        return {
            'answer': "Insufficient evidence: Unable to correlate suspects with available evidence. "
                     "The evidence may not contain sufficient information about the suspects.",
            'ranked': ranked,
            'components': {'docs_used': len(docs)}
        }
    

    lines = []
    

    if ranked and len(ranked) > 0:
        top_suspect = ranked[0]
        lines.append(f"## 🔍 Analysis Result\n")
        lines.append(f"**{top_suspect['suspect_name']}** has the strongest evidence correlation (score: {top_suspect['score']:.2f}).\n")
        

        if top_suspect['matched_clues']:
            lines.append("**Key evidence:**")
            for clue in top_suspect['matched_clues'][:3]:
                lines.append(f"- {clue}")
            lines.append("")
        

        if len(ranked) > 1:
            other_suspects = [s for s in ranked[1:] if s['score'] > 0]
            if other_suspects:
                lines.append("**Other suspects:**")
                for suspect in other_suspects[:2]:
                    lines.append(f"- {suspect['suspect_name']} (score: {suspect['score']:.2f})")
                lines.append("")
    

    lines.append("⚠️ *This analysis is decision support only, not a legal conclusion. All suspects are presumed innocent.*")
    
    answer = "\n".join(lines)
    
    logger.info(f"✅ Ranked {len(ranked)} suspects")
    

    if user_id:
        save_chat_message(user_id, answer, False, case_id)
    
    return {
        'answer': answer,
        'ranked': ranked,
        'tools_used': [],
        'components': {
            'docs_used': len(docs),
            'suspects_analyzed': len(ranked)
        }
    }






def answer_question(
    case_id: int,
    user_query: str,
    k: Optional[int] = None,
    temperature: float = 0.2,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point: routes query to appropriate handler
    
    Args:
        case_id: Case ID
        user_query: User's question
        k: Number of documents to retrieve. If None, uses total indexed documents for the case (capped at 30)
        temperature: LLM temperature
        user_id: Optional user identifier for memory system
        
    Returns:
        Result dictionary from appropriate handler (answer_general or answer_rank_suspects)
        
    Example:
        >>> # Suspect ranking query
        >>> result = answer_question(case_id=1, user_query="Who is most likely guilty?", user_id="user_123")
        >>> print(result['answer'])
        >>> print(result.get('ranked', []))
        
        >>> # General query
        >>> result = answer_question(case_id=1, user_query="What vehicle was used?", user_id="user_123")
        >>> print(result['answer'])
    """
    logger.info(f"❓ Processing query for case {case_id}: {user_query}")
    

    if user_id:
        save_chat_message(user_id, user_query, True, case_id)
    

    if user_id:
        memory_items = extract_memory(user_query)
        if memory_items:
            for key, value in memory_items:
                save_memory(user_id, key, value)

            logger.info(f"💾 Saved {len(memory_items)} memory items for user {user_id}")
            answer_text = "Got it — I'll remember that."

            save_chat_message(user_id, answer_text, False, case_id)
            return {
                'answer': answer_text,
                'context_used': False,
                'memory_saved': True
            }
        

        memory_key = is_memory_question(user_query)
        if memory_key is not None:
            if memory_key:
                value = get_memory(user_id, memory_key)
                if value:
                    logger.info(f"💭 Retrieved memory for user {user_id}, key={memory_key}")
                    answer_text = f"Your {memory_key} is {value}."

                    save_chat_message(user_id, answer_text, False, case_id)
                    return {
                        'answer': answer_text,
                        'context_used': False,
                        'memory_retrieved': True
                    }
                else:
                    answer_text = f"I don't have your {memory_key} stored. You can tell me by saying something like 'my {memory_key} is X'."
                    save_chat_message(user_id, answer_text, False, case_id)
                    return {
                        'answer': answer_text,
                        'context_used': False,
                        'memory_retrieved': False
                    }
            else:
                all_memory = load_all_memory(user_id)
                if all_memory:
                    memory_list = "\n".join([f"- {k}: {v}" for k, v in all_memory.items()])
                    answer_text = f"Here's what I remember about you:\n{memory_list}"
                else:
                    answer_text = "I don't have any information stored about you yet. You can tell me things like 'my name is X' or 'I live in Y'."
                save_chat_message(user_id, answer_text, False, case_id)
                return {
                    'answer': answer_text,
                    'context_used': False,
                    'memory_retrieved': bool(all_memory)
                }
    


    query_lower = user_query.lower()
    tool_keywords = ['summary', 'overview', 'case info', 'what is the case', 'tell me about the case', 
                     'case details', 'case summary', 'extract timeline', 'analyze timeline', 'timeline events',
                     'what is the timeline', 'show timeline', 'timeline of events', 'sequence of events', 'chronology']
    is_tool_query = any(keyword in query_lower for keyword in tool_keywords)
    

    if not is_tool_query and is_simple_fact_query(user_query):
        logger.info("📝 Detected simple fact query - using concise answer mode")
        return answer_simple_fact(case_id, user_query, k=k, temperature=temperature, user_id=user_id)
    

    intent_result = detect_intent(user_query)
    intent = intent_result['intent']
    
    logger.info(f"🎯 Detected intent: {intent} (confidence: {intent_result['confidence']:.2f})")
    

    if intent == 'rank_suspects':
        return answer_rank_suspects(case_id, query=user_query, k=k, user_id=user_id)
    else:

        return answer_general(case_id, user_query, k=k, temperature=temperature, user_id=user_id)






def to_markdown(result: Dict[str, Any]) -> str:
    """
    Format result dictionary as markdown for Streamlit
    
    Args:
        result: Result from answer_question()
        
    Returns:
        Markdown-formatted string
        
    Example:
        >>> result = answer_question(case_id=1, user_query="Who is guilty?")
        >>> print(to_markdown(result))
    """
    lines = []
    

    lines.append("## Analysis Result\n")
    lines.append(result.get('answer', 'No answer generated'))
    lines.append("\n---\n")
    

    if result.get('components'):
        lines.append("### 📊 Analysis Metadata\n")
        for key, value in result['components'].items():
            lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        lines.append("")
    
    return "\n".join(lines)



if __name__ == "__main__":
    """
    Quick test of forensic agent
    Run with: python -m app.agent.forensic_agent
    """
    print("=" * 60)
    print("Forensic Agent Test")
    print("=" * 60)
    
    from app.db import get_all_cases
    

    if not Config.GEMINI_API_KEY:
        print("\n❌ GEMINI_API_KEY not configured in .env")
        print("Add it to continue: GEMINI_API_KEY=your_api_key")
        exit(1)
    
    cases = get_all_cases()
    
    if not cases:
        print("\n⚠️  No cases found in database")
        print("Run: python example_db_usage.py to create sample data")
        exit(0)
    

    case_with_data = None
    for case in cases:
        status = get_case_index_status(case.id)
        suspects = get_suspects_by_case(case.id)
        
        if status.get('indexed') and suspects:
            case_with_data = case
            break
    
    if not case_with_data:
        print("\n⚠️  No cases with evidence and suspects found")
        exit(0)
    
    print(f"\n📁 Testing with case: {case_with_data.title}")
    

    print("\n🧪 Testing intent detection...")
    test_queries = [
        "Who is the most likely suspect?",
        "Summarize the evidence",
        "What vehicle was used?"
    ]
    
    for query in test_queries:
        intent = detect_intent(query)
        print(f"   '{query}' → {intent['intent']}")
    

    print("\n🤔 Testing general Q&A...")
    result = answer_general(case_with_data.id, "What evidence do we have?", k=3)
    print(f"   Answer length: {len(result['answer'])} chars")
    

    print("\n🎯 Testing suspect ranking...")
    result = answer_rank_suspects(case_with_data.id)
    print(f"   Ranked suspects: {len(result.get('ranked', []))}")
    
    print("\n✅ Forensic agent test complete!")

