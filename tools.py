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
            print(f"MATH TOOL DEBUG - Starting calculation")
            print(f"   Original expression: '{expression}'")
        
        expression = expression.strip()
        
        if debugging:
            print(f"   Cleaned expression: '{expression}'")
        
        safe_dict = {

            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow,
            
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "asin": math.asin, "acos": math.acos, "atan": math.atan,
            "log": math.log, "log10": math.log10, "exp": math.exp,
            "floor": math.floor, "ceil": math.ceil,
            "degrees": math.degrees, "radians": math.radians,
            "factorial": math.factorial,
            
            "pi": math.pi, "e": math.e,
            
            "__builtins__": {}
        }
        
        original_expr = expression
        expression = expression.replace("^", "**")
        expression = expression.replace("×", "*")
        expression = expression.replace("÷", "/")
        
        if debugging and original_expr != expression:
            print(f"   Symbol replacement: '{original_expr}' → '{expression}'")
        
        if debugging:
            print(f"   Evaluating with safe environment...")
        
        result = eval(expression, safe_dict)
        
        if debugging:
            print(f"    MATH SUCCESS: {expression} = {result} (type: {type(result).__name__})")
        
        return {
            "expression": expression,
            "result": result,
            "success": True,
            "type": type(result).__name__
        }
        
    except ZeroDivisionError:
        if debugging:
            print(f"    MATH ERROR: Division by zero")
        return {
            "expression": expression,
            "error": "Division by zero",
            "success": False
        }
    except OverflowError:
        if debugging:
            print(f"    MATH ERROR: Result too large")
        return {
            "expression": expression,
            "error": "Result too large",
            "success": False
        }
    except (SyntaxError, NameError, TypeError) as e:
        if debugging:
            print(f"    MATH ERROR: Invalid expression - {str(e)}")
        return {
            "expression": expression,
            "error": f"Invalid expression: {str(e)}",
            "success": False
        }
    except Exception as e:
        if debugging:
            print(f"    MATH ERROR: Unexpected error - {str(e)}")
        return {
            "expression": expression,
            "error": f"Calculation error: {str(e)}",
            "success": False
        }

def search_web(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using multiple strategies for better results
    """
    try:
        if debugging:
            print(f"WEB SEARCH DEBUG - Starting search")
            print(f"   Query: '{query}'")
            print(f"   Max results: {num_results}")
        
        original_query = query
        query = query.strip()
        
        search_prefixes = ["search", "find", "look for", "search for", "look up", "google"]
        query_lower = query.lower()
        
        for prefix in search_prefixes:
            patterns = [
                f"{prefix} \"",
                f"{prefix} '",
                f"{prefix} ",
            ]
            for pattern in patterns:
                if query_lower.startswith(pattern):
                    old_query = query
                    if pattern.endswith('"') or pattern.endswith("'"):

                        quote_char = pattern[-1]
                        if query.endswith(quote_char):
                            query = query[len(pattern):-1].strip()
                        else:
                            query = query[len(pattern):].strip()
                    else:
                        query = query[len(pattern):].strip()
                    
                    if debugging:
                        print(f"   Removed search prefix: '{old_query}' → '{query}'")
                    break
        
        web_suffixes = ["on the web", "in web", "on web", "online", "on internet"]
        for suffix in web_suffixes:
            if query_lower.endswith(suffix):
                old_query = query
                query = query[:-len(suffix)].strip()
                if debugging:
                    print(f"   Removed web suffix: '{old_query}' → '{query}'")
                break
        
        if query.startswith('"') and query.endswith('"') and query.count('"') == 2:
            old_query = query
            query = query[1:-1].strip()
            if debugging:
                print(f"   Removed surrounding quotes: '{old_query}' → '{query}'")
        
        num_results = max(1, min(num_results, 10))
        
        if not query:
            if debugging:
                print(f"    SEARCH ERROR: Empty query after cleaning")
            return {
                "query": original_query,
                "error": "Empty search query after cleaning",
                "success": False
            }
        
        if debugging:
            print(f"   Final cleaned query: '{query}'")
        
        try:
            if debugging:
                print(f"   Strategy 1: DuckDuckGo Instant Answer API")
            
            ddg_url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
                "no_redirect": "1",
                "safe_search": "moderate"
            }
            
            if debugging:
                print(f"   Making request to: {ddg_url}")
                print(f"   Parameters: {params}")
            
            response = requests.get(ddg_url, params=params, timeout=8,
                                  headers={'User-Agent': 'Mozilla/5.0 (compatible; SearchBot/1.0)'})
            
            if debugging:
                print(f"   Response status: {response.status_code}")
                print(f"   Response length: {len(response.text)} characters")
            
            response.raise_for_status()
            
            if response.text.strip():
                try:
                    data = response.json()
                    if debugging:
                        print(f"    JSON parsed successfully")
                        print(f"   Response keys: {list(data.keys())}")
                    
                    meta = data.get('meta', {})
                    if (meta.get('name') == 'Just Another Test' or
                        meta.get('id') == 'just_another_test' or
                        meta.get('production_state') == 'offline'):
                        if debugging:
                            print(f"    Detected test response, skipping DuckDuckGo API")
                        raise ValueError("Test response detected")
                    
                    results = []
                    
                    if data.get("AbstractText") and len(data.get("AbstractText", "").strip()) > 10:
                        if debugging:
                            print(f"   Found instant answer: {data.get('Heading', 'No heading')}")
                        results.append({
                            "title": data.get("Heading", query.title()),
                            "snippet": data.get("AbstractText", ""),
                            "url": data.get("AbstractURL", ""),
                            "source": "DuckDuckGo Instant Answer"
                        })
                    
                    if data.get("Definition") and len(data.get("Definition", "").strip()) > 10:
                        if debugging:
                            print(f"   Found definition")
                        results.append({
                            "title": f"Definition: {query}",
                            "snippet": data.get("Definition", ""),
                            "url": data.get("DefinitionURL", ""),
                            "source": "DuckDuckGo Definition"
                        })
                    
                    related_topics = data.get("RelatedTopics", [])
                    if related_topics:
                        if debugging:
                            print(f"   Found {len(related_topics)} related topics")
                        for i, topic in enumerate(related_topics[:num_results-len(results)]):
                            if isinstance(topic, dict) and topic.get("Text"):
                                text = topic.get("Text", "")
                                if len(text.strip()) > 20:
                                    if debugging:
                                        print(f"     Topic {i+1}: {text[:50]}...")
                                    
                                    title = query.title()
                                    if topic.get("Result"):
                                        result_text = topic.get("Result", "")
                                        if " - " in result_text:
                                            title = result_text.split(" - ")[0]
                                        elif len(result_text) < 100:
                                            title = result_text
                                    
                                    results.append({
                                        "title": title,
                                        "snippet": text,
                                        "url": topic.get("FirstURL", ""),
                                        "source": "DuckDuckGo Related"
                                    })
                    
                    if results:
                        if debugging:
                            print(f"    STRATEGY 1 SUCCESS: Found {len(results)} results")
                            for i, result in enumerate(results, 1):
                                print(f"     Result {i}: {result['title']}")
                        
                        return {
                            "query": query,
                            "original_query": original_query,
                            "results": results[:num_results],
                            "total_results": len(results),
                            "success": True,
                            "source": "DuckDuckGo API"
                        }
                    else:
                        if debugging:
                            print(f"    Strategy 1: No meaningful results found")
                
                except ValueError as json_error:
                    if debugging:
                        print(f"    Strategy 1 JSON ERROR: {json_error}")

        except (requests.RequestException, ValueError) as e:
            if debugging:
                print(f"    Strategy 1 ERROR: {e}")
        
        if any(tld in query.lower() for tld in ['.com', '.org', '.net', '.edu', '.gov', '.io', '.co']):
            if debugging:
                print(f"   Strategy 2: Domain-specific search")
            
            domain_match = re.search(r'([a-zA-Z0-9-]+\.(?:com|org|net|edu|gov|io|co|uk|de|fr|tr))', query.lower())
            if domain_match:
                domain = domain_match.group(1)
                
                results = [
                    {
                        "title": f"Visit {domain}",
                        "snippet": f"To visit {domain}, you can go directly to https://{domain} or http://{domain}. This appears to be a website domain.",
                        "url": f"https://{domain}",
                        "source": "Domain suggestion"
                    },
                    {
                        "title": f"Information about {domain}",
                        "snippet": f"For information about {domain}, you could check: 1) The website directly, 2) WHOIS databases, 3) Web archives, or 4) Search engines like Google.",
                        "url": f"https://www.google.com/search?q={domain}",
                        "source": "Domain research guidance"
                    }
                ]
                
                if debugging:
                    print(f"    STRATEGY 2 SUCCESS: Created domain-specific results for {domain}")
                
                return {
                    "query": query,
                    "original_query": original_query,
                    "results": results,
                    "total_results": len(results),
                    "success": True,
                    "source": "Domain-specific search"
                }
        
        if debugging:
            print(f"   Strategy 3: Enhanced fallback guidance")
        
        fallback_message = f"I would search for '{query}' but don't have access to live web search at the moment."
        search_suggestions = []
        
        query_lower = query.lower()
        
        if any(term in query_lower for term in ["exchange rate", "currency", "usd", "try", "eur", "gbp", "bitcoin", "crypto"]):
            guidance_type = "currency/finance"
            fallback_message += " For current financial information, I recommend:"
            search_suggestions = [
                "XE.com for exchange rates",
                "Google Finance or Yahoo Finance",
                "CoinMarketCap for cryptocurrency",
                "Your bank's website for official rates"
            ]
        elif any(term in query_lower for term in ["news", "latest", "current", "recent", "breaking"]):
            guidance_type = "news"
            fallback_message += " For latest news, try:"
            search_suggestions = [
                "Google News (news.google.com)",
                "BBC News (bbc.com/news)",
                "Reuters (reuters.com)",
                "Associated Press (apnews.com)"
            ]
        elif any(term in query_lower for term in ["weather", "temperature", "forecast", "climate"]):
            guidance_type = "weather"
            fallback_message += " For weather information, check:"
            search_suggestions = [
                "Weather.com",
                "AccuWeather.com",
                "Google Weather (search 'weather [location]')",
                "Your local meteorological service"
            ]
        elif any(term in query_lower for term in ["stock", "share", "market", "trading", "nasdaq", "dow"]):
            guidance_type = "stocks"
            fallback_message += " For stock market information:"
            search_suggestions = [
                "Yahoo Finance (finance.yahoo.com)",
                "Google Finance",
                "Bloomberg (bloomberg.com)",
                "MarketWatch (marketwatch.com)"
            ]
        elif any(term in query_lower for term in ["recipe", "cooking", "ingredient", "food"]):
            guidance_type = "recipes"
            fallback_message += " For recipes and cooking information:"
            search_suggestions = [
                "AllRecipes (allrecipes.com)",
                "Food Network (foodnetwork.com)",
                "BBC Good Food",
                "Serious Eats (seriouseats.com)"
            ]
        else:
            guidance_type = "general"
            fallback_message += " You can search for this on:"
            search_suggestions = [
                "Google (google.com)",
                "DuckDuckGo (duckduckgo.com)",
                "Bing (bing.com)",
                "Specialized search engines for your topic"
            ]
        
        if search_suggestions:
            fallback_message += "\n• " + "\n• ".join(search_suggestions)
        
        if debugging:
            print(f"   Guidance type: {guidance_type}")
            print(f"   Suggestions count: {len(search_suggestions)}")
        
        result = {
            "query": query,
            "original_query": original_query,
            "results": [
                {
                    "title": f"Search guidance for: {query}",
                    "snippet": fallback_message,
                    "url": f"https://www.google.com/search?q={query.replace(' ', '+')}",
                    "source": "Search guidance"
                }
            ],
            "total_results": 1,
            "success": True,
            "source": "Enhanced fallback guidance",
            "note": "Live web search not available - providing enhanced search guidance",
            "guidance_type": guidance_type
        }
        
        if debugging:
            print(f"    STRATEGY 3 SUCCESS: Returning enhanced guidance for {guidance_type} query")
        
        return result
        
    except Exception as e:
        if debugging:
            print(f"    SEARCH ERROR: Unexpected error - {str(e)}")
            import traceback
            print(f"   Full traceback:")
            traceback.print_exc()
        
        return {
            "query": query,
            "original_query": original_query if 'original_query' in locals() else query,
            "error": f"Search error: {str(e)}",
            "success": False
        }

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
        print(f"TOOL EXECUTION DEBUG")
        print(f"   Function: {function_name}")
        print(f"   Parameters: {parameters}")
        print(f"   Available tools: {list(TOOL_FUNCTIONS.keys())}")
    
    if function_name not in TOOL_FUNCTIONS:
        if debugging:
            print(f"    TOOL ERROR: Function '{function_name}' not found")
        return {
            "error": f"Tool '{function_name}' not found. Available tools: {list(TOOL_FUNCTIONS.keys())}",
            "success": False
        }
    
    try:
        function = TOOL_FUNCTIONS[function_name]
        if debugging:
            print(f"    Function found, executing...")
        
        result = function(**parameters)
        
        if debugging:
            print(f"    TOOL SUCCESS: Execution completed")
            if isinstance(result, dict):
                if result.get("success"):
                    print(f"     Result type: {type(result.get('result', 'N/A'))}")
                    if function_name == "calculate_math":
                        print(f"     Math result: {result.get('result')}")
                    elif function_name == "search_web":
                        print(f"     Search results count: {result.get('total_results', 0)}")
                else:
                    print(f"     Tool reported failure: {result.get('error', 'Unknown error')}")
        
        return result
        
    except TypeError as e:
        if debugging:
            print(f"    PARAMETER ERROR: {str(e)}")
        return {
            "error": f"Invalid parameters for {function_name}: {str(e)}",
            "success": False
        }
    except Exception as e:
        if debugging:
            print(f"    EXECUTION ERROR: {str(e)}")
            import traceback
            print(f"   Full traceback:")
            traceback.print_exc()
        return {
            "error": f"Error executing {function_name}: {str(e)}",
            "success": False
        }
