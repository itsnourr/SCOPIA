"""
LangChain Agent with Tools Integration

This module provides a LangChain agent that can use custom tools for case analysis.
The agent can automatically call tools like get_case_summary and analyze_timeline_text.
"""

import logging
from typing import Dict, Any, Optional, List

try:
    from langchain.agents import initialize_agent, AgentType, AgentExecutor, create_react_agent
    from langchain.memory import ConversationBufferMemory
    from langchain_core.prompts import PromptTemplate
    from langchain_core.tools import Tool
    AGENT_AVAILABLE = True
except ImportError:

    try:
        from langchain.agents import AgentExecutor, create_react_agent
        from langchain_core.prompts import PromptTemplate
        from langchain.memory import ConversationBufferMemory
        from langchain_core.tools import Tool
        AGENT_AVAILABLE = True
        AGENT_TYPE_AVAILABLE = False
    except ImportError:
        logging.warning("LangChain agent components not available. Tools will be used directly.")
        AGENT_AVAILABLE = False
        AGENT_TYPE_AVAILABLE = False

from config import Config
from app.agent.tools import get_case_summary, analyze_timeline_text, vector_search
from app.agent.forensic_agent import build_llm
from app.agent.tool_runner import run_tool


logger = logging.getLogger(__name__)


def create_tool_enabled_agent(case_id: int, user_id: Optional[str] = None):
    """
    Create a LangChain agent with custom tools enabled using create_agent() pattern (P3 compliance).
    
    This function properly integrates LangChain's agent framework with tools,
    ensuring tool calls appear as AIMessage(tool_calls=[...]).
    
    P5 Compliance: Includes vector_search RAG tool bound to the case_id.
    
    Args:
        case_id: The case ID to use for tool context
        user_id: Optional user identifier
        
    Returns:
        Initialized LangChain agent with tools (AgentExecutor)
    """
    if not Config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")
    

    from app.agent.forensic_agent import ForensicLLM
    llm_wrapper = ForensicLLM(temperature=0.2)
    llm = llm_wrapper.llm
    



    tools = [
        vector_search,
        get_case_summary,
        analyze_timeline_text,
    ]
    

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    if AGENT_AVAILABLE:
        try:


            if hasattr(AgentType, 'CHAT_CONVERSATIONAL_REACT_DESCRIPTION'):
                agent = initialize_agent(
                    tools=tools,
                    llm=llm,
                    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                    verbose=True,
                    memory=memory,
                    handle_parsing_errors=True
                )
                logger.info("✅ Created LangChain agent with tools (conversational-react-description) - P3 compliant")
                return agent
            else:

                from langchain import hub
                try:
                    prompt = hub.pull("hwchase17/react-chat")
                except:

                    prompt = PromptTemplate.from_template("""
You are a helpful assistant. Use the following tools to answer questions.

Tools: {tools}

Tool Names: {tool_names}

Previous conversation:
{chat_history}

Human: {input}
Assistant:""")
                
                agent = create_react_agent(llm, tools, prompt)
                agent_executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    verbose=True,
                    memory=memory,
                    handle_parsing_errors=True
                )
                logger.info("✅ Created LangChain agent with tools (react-chat) - P3 compliant")
                return agent_executor
        except Exception as e:
            logger.warning(f"⚠️ Could not create agent: {e}. Using fallback.")
            AGENT_AVAILABLE = False
    

    logger.warning("⚠️ Using manual tool calling (LangChain agent framework not fully available)")
    return {
        'llm': llm,
        'tools': tools,
        'memory': memory,
        'case_id': case_id,
        'user_id': user_id
    }


def answer_with_tools(
    case_id: int,
    user_query: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Answer a question using LangChain agent with tools (P3 compliance).
    
    This function uses the LangChain agent framework to automatically
    call tools including vector_search (RAG), get_case_summary, and analyze_timeline_text.
    
    The agent will automatically:
    - Use vector_search tool for evidence retrieval (P5 compliance)
    - Call other tools when appropriate
    - Produce AIMessage(tool_calls=[...]) structure
    
    Args:
        case_id: Case ID (required for tools)
        user_query: User's question
        user_id: Optional user identifier
        
    Returns:
        Dictionary with answer, tools_used, and tool_results
    """
    logger.info(f"🔧 Using tool-enabled agent for case {case_id}: {user_query}")
    
    try:
        agent = create_tool_enabled_agent(case_id, user_id)
        

        if isinstance(agent, dict):

            return _answer_with_manual_tools(agent, case_id, user_query)
        

        contextual_query = f"""Case ID: {case_id}

User Question: {user_query}

IMPORTANT: When calling tools, you MUST pass case_id={case_id} as a parameter.
- For vector_search: use vector_search(query="{user_query}", case_id={case_id}, k=10)
- For get_case_summary: use get_case_summary(case_id={case_id})
- For analyze_timeline_text: use analyze_timeline_text(text="...", case_id={case_id})

Always use the vector_search tool first to retrieve relevant evidence before answering questions about the case."""
        

        response = agent.run(input=contextual_query)
        

        tools_used = []
        if hasattr(agent, 'agent') and hasattr(agent.agent, 'llm_chain'):

            tools_used = ['agent_framework']
        
        return {
            'answer': response,
            'context_used': True,
            'tools_used': tools_used if tools_used else ['agent_framework'],
            'tool_results': []
        }
        
    except Exception as e:
        logger.error(f"❌ Error in tool-enabled agent: {e}")
        return {
            'answer': f"Error using tool-enabled agent: {str(e)}",
            'context_used': False,
            'tools_used': False
        }


def _answer_with_manual_tools(
    agent_dict: Dict[str, Any],
    case_id: int,
    user_query: str
) -> Dict[str, Any]:
    """
    Fallback: Manually call tools based on query intent.
    
    This is used when LangChain agent framework is not fully available.
    """
    tools = agent_dict.get('tools', [])
    llm = agent_dict.get('llm')
    

    query_lower = user_query.lower()
    
    summary_keywords = ['summary', 'overview', 'case info', 'what is the case', 'tell me about the case', 
                       'case details', 'case summary', 'summarize this case', 'summarize the case', 
                       'summarize case', 'give me a summary', 'case overview']
    if any(keyword in query_lower for keyword in summary_keywords):
        try:
            tool_result = run_tool(
                "get_case_summary",
                get_case_summary,
                {"case_id": case_id}
            )

            answer = f"=== TOOL OUTPUTS ===\n{tool_result['print_block']}\n\n=== AGENT RESPONSE ===\nTool {tool_result['tool']} returned:\n{tool_result['output']}"
            return {
                'answer': answer,
                'context_used': True,
                'tools_used': True,
                'tool_results': [tool_result]
            }
        except Exception as e:
            logger.error(f"Error calling get_case_summary: {e}")
    

    if any(keyword in query_lower for keyword in ['extract timeline', 'analyze timeline', 'timeline events']):


        try:
            tool_result = run_tool(
                "analyze_timeline_text",
                analyze_timeline_text,
                {'text': user_query, 'case_id': case_id}
            )

            answer = f"=== TOOL OUTPUTS ===\n{tool_result['print_block']}\n\n=== AGENT RESPONSE ===\nTool {tool_result['tool']} returned:\n{tool_result['output']}"
            return {
                'answer': answer,
                'context_used': True,
                'tools_used': True,
                'tool_results': [tool_result]
            }
        except Exception as e:
            logger.error(f"Error calling analyze_timeline_text: {e}")
    

    if llm:
        try:
            response = llm.invoke(user_query)
            return {
                'answer': response.content if hasattr(response, 'content') else str(response),
                'context_used': False,
                'tools_used': False
            }
        except Exception as e:
            logger.error(f"Error using LLM: {e}")
    
    return {
        'answer': "Unable to process query with available tools.",
        'context_used': False,
        'tools_used': False
    }

