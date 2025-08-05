"""
Tools module for the chatbot - provides web search and math calculation capabilities
"""
import json
import requests
import math
import re
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()
debugging = os.getenv("debugging", "false").lower() == "true"

def calculate_math(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate mathematical expressions
    Supports basic arithmetic, trigonometry, logarithms, and constants
    """
    try:
        if debugging:
            print(f"Calculating math expression: {expression}")
        
        # Clean the expression
        expression = expression.strip()
        
        # Create a safe environment for evaluation
        safe_dict = {
            # Basic functions
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow,
            
            # Math module functions
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "asin": math.asin, "acos": math.acos, "atan": math.atan,
            "log": math.log, "log10": math.log10, "exp": math.exp,
            "floor": math.floor, "ceil": math.ceil,
            "degrees": math.degrees, "radians": math.radians,
            "factorial": math.factorial,
            
            # Constants
            "pi": math.pi, "e": math.e,
            
            # Prevent access to builtins
            "__builtins__": {}
        }
        
        # Replace common math symbols with Python equivalents
        expression = expression.replace("^", "**")  # Power operator
        expression = expression.replace("×", "*")   # Multiplication
        expression = expression.replace("÷", "/")   # Division
        
        # Evaluate the expression
        result = eval(expression, safe_dict)
        
        if debugging:
            print(f"Math calculation result: {result}")
        
        return {
            "expression": expression,
            "result": result,
            "success": True,
            "type": type(result).__name__
        }
        
    except ZeroDivisionError:
        return {
            "expression": expression,
            "error": "Division by zero",
            "success": False
        }
    except OverflowError:
        return {
            "expression": expression,
            "error": "Result too large",
            "success": False
        }
    except (SyntaxError, NameError, TypeError) as e:
        return {
            "expression": expression,
            "error": f"Invalid expression: {str(e)}",
            "success": False
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": f"Calculation error: {str(e)}",
            "success": False
        }

def search_web(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using DuckDuckGo Instant Answer API
    Falls back to a simple search results format
    """
    try:
        if debugging:
            print(f"Searching web for: {query}")
        
        # Clean and validate inputs
        query = query.strip()
        num_results = max(1, min(num_results, 10))  # Limit between 1-10
        
        if not query:
            return {
                "query": query,
                "error": "Empty search query",
                "success": False
            }
        
        # Try DuckDuckGo Instant Answer API first
        try:
            ddg_url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            response = requests.get(ddg_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Check for instant answer
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", query),
                    "snippet": data.get("AbstractText", ""),
                    "url": data.get("AbstractURL", ""),
                    "source": "DuckDuckGo Instant Answer"
                })
            
            # Check for related topics
            if data.get("RelatedTopics"):
                for topic in data.get("RelatedTopics", [])[:num_results-len(results)]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append({
                            "title": topic.get("Result", "").split(" - ")[0] if " - " in topic.get("Result", "") else query,
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "source": "DuckDuckGo Related"
                        })
            
            # If we got results, return them
            if results:
                if debugging:
                    print(f"Found {len(results)} web search results")
                
                return {
                    "query": query,
                    "results": results[:num_results],
                    "total_results": len(results),
                    "success": True,
                    "source": "DuckDuckGo API"
                }
        
        except requests.RequestException as e:
            if debugging:
                print(f"DuckDuckGo API error: {e}")
        
        # Fallback: Return helpful message about search
        return {
            "query": query,
            "results": [
                {
                    "title": f"Search suggestion for: {query}",
                    "snippet": f"I would search for '{query}' but don't have access to live web search. "
                              f"You can search for this on Google, Bing, or DuckDuckGo.",
                    "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                    "source": "Search suggestion"
                }
            ],
            "total_results": 1,
            "success": True,
            "source": "Fallback suggestion",
            "note": "Live web search not available - this is a search suggestion"
        }
        
    except Exception as e:
        if debugging:
            print(f"Web search error: {e}")
        
        return {
            "query": query,
            "error": f"Search error: {str(e)}",
            "success": False
        }

# Tool definitions for Gemini API
AVAILABLE_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "calculate_math",
                "description": "Perform mathematical calculations and evaluate expressions. Supports arithmetic, trigonometry, logarithms, and common math functions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate. Examples: '2+2', 'sqrt(16)', 'sin(pi/2)', '5!', 'log(100)', '2^3'"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "search_web",
                "description": "Search the web for current information on any topic. Returns relevant results with titles, snippets, and URLs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query or question to find information about"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of search results to return (1-10, default: 5)",
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    }
]

# Function mapping for tool execution
TOOL_FUNCTIONS = {
    "calculate_math": calculate_math,
    "search_web": search_web
}

def execute_tool(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool function with given parameters
    
    Args:
        function_name: Name of the function to execute
        parameters: Dictionary of parameters to pass to the function
        
    Returns:
        Dictionary containing the result or error information
    """
    if debugging:
        print(f"Executing tool: {function_name} with parameters: {parameters}")
    
    if function_name not in TOOL_FUNCTIONS:
        return {
            "error": f"Tool '{function_name}' not found. Available tools: {list(TOOL_FUNCTIONS.keys())}",
            "success": False
        }
    
    try:
        function = TOOL_FUNCTIONS[function_name]
        result = function(**parameters)
        
        if debugging:
            print(f"Tool execution result: {result}")
        
        return result
        
    except TypeError as e:
        return {
            "error": f"Invalid parameters for {function_name}: {str(e)}",
            "success": False
        }
    except Exception as e:
        return {
            "error": f"Error executing {function_name}: {str(e)}",
            "success": False
        }
