"""
Tool Runner for P7 Compliance

This module provides a unified wrapper function for executing tools
with standardized output formatting that matches P7_PrintToolOutputs pattern.

Every tool call must display:
> Entering tool: {tool_name}
{input_data}
{output}
> Exiting tool: {tool_name}

This format is:
- Printed to console logs
- Returned to UI as part of agent response
- Appended to chat history as its own message block
"""

import logging
from typing import Dict, Any, Callable


logger = logging.getLogger(__name__)


def run_tool(tool_name: str, tool_func: Callable, input_data: dict) -> Dict[str, Any]:
    """
    Execute a tool with standardized P7-compliant output formatting.
    
    This function wraps tool execution to ensure all tool calls follow
    the P7_PrintToolOutputs pattern:
    
    > Entering tool: {tool_name}
    {input_data}
    {output}
    > Exiting tool: {tool_name}
    
    Args:
        tool_name: Name of the tool being executed
        tool_func: The tool function to execute
        input_data: Dictionary of input parameters for the tool
        
    Returns:
        Dictionary containing:
            - tool: Tool name
            - input: Input data dictionary
            - output: Tool output result
            - print_block: Formatted string block for display/storage
            
    Example:
        >>> from app.agent.tools import get_case_summary
        >>> result = run_tool(
        ...     "get_case_summary",
        ...     get_case_summary,
        ...     {"case_id": 1}
        ... )
        >>> print(result["print_block"])
        > Entering tool: get_case_summary
        {'case_id': 1}
        Case: Murder at Oak Street...
        > Exiting tool: get_case_summary
    """

    print(f"> Entering tool: {tool_name}")
    logger.info(f"> Entering tool: {tool_name}")
    

    print(input_data)
    logger.debug(f"Tool input: {input_data}")
    

    try:

        if hasattr(tool_func, 'invoke'):

            result = tool_func.invoke(input_data)
        else:

            result = tool_func(**input_data)
        

        print(result)
        logger.info(f"Tool output: {result}")
        
    except Exception as e:
        error_msg = f"Error executing tool {tool_name}: {str(e)}"
        print(error_msg)
        logger.error(error_msg, exc_info=True)
        result = error_msg
    

    print(f"> Exiting tool: {tool_name}")
    logger.info(f"> Exiting tool: {tool_name}")
    



    input_str = str(input_data)
    result_str = str(result)
    print_block = f"> Entering tool: {tool_name}\n{input_str}\n{result_str}\n> Exiting tool: {tool_name}"
    
    return {
        "tool": tool_name,
        "input": input_data,
        "output": result,
        "print_block": print_block
    }

