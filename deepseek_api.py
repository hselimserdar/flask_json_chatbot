import os
import re
import json
import requests
from dotenv import load_dotenv
from typing import List, Dict
from tools import AVAILABLE_TOOLS, execute_tool

load_dotenv()
debugging = os.getenv("debugging", "false").lower() == "true"

def call_deepseek_api(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    temperature: float = 0.3,
    candidate_count: int = 1,
    use_tools: bool = False
) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set")

    openai_messages = []
    for m in messages:
        role = "user" if m["author"] in ["user", "system"] else "assistant"
        openai_messages.append({
            "role": role,
            "content": m["content"]
        })

    try:
        if use_tools and openai_messages:
            if debugging:
                print(f" DEEPSEEK API DEBUG - Tool processing enabled")
            
            full_message = openai_messages[-1]["content"]
            
            if debugging:
                print(f"   Full message length: {len(full_message)} characters")
                print(f"   Full message preview: {full_message[:100]}...")
            
            user_message = full_message
            if "Current message:" in full_message:
                current_msg_match = re.search(r"Current message:\s*(.+?)(?:\n\n|$)", full_message, re.DOTALL)
                if current_msg_match:
                    user_message = current_msg_match.group(1).strip()
                    if debugging:
                        print(f"   Extracted current message: '{user_message}'")
            elif "User message:" in full_message:
                user_msg_match = re.search(r"User message:\s*(.+?)(?:\n\n|$)", full_message, re.DOTALL)
                if user_msg_match:
                    user_message = user_msg_match.group(1).strip()
                    if debugging:
                        print(f"   Extracted user message: '{user_message}'")
            else:
                if debugging:
                    print(f"   Using full message as user message")
            
            user_message_lower = user_message.lower()
            
            if debugging:
                print(f"   Analyzing message: '{user_message}'")
            
            search_keywords = [
                "search web", "web search", "search for", "look up", 
                "find information", "current", "latest", "recent", 
                "what is the", "exchange rate", "news about", "information about",
                "find", "search", "whats"
            ]
            
            found_keywords = [kw for kw in search_keywords if kw in user_message_lower]
            should_search = len(found_keywords) > 0 and (
                "search" in user_message_lower or 
                "find" in user_message_lower or 
                "current" in user_message_lower or
                "latest" in user_message_lower or
                "what is" in user_message_lower
            )
            
            if debugging:
                print(f"   Search keywords found: {found_keywords}")
                print(f"   Should search: {should_search}")
            
            if should_search:
                if debugging:
                    print(f"    INITIATING WEB SEARCH")
                
                search_query = user_message
                
                if debugging:
                    print(f"   Original search query: '{search_query}'")
                
                patterns_to_remove = [
                    r"search\s+(web\s+)?for\s+",
                    r"look\s+up\s+",
                    r"find\s+information\s+(about\s+)?",
                    r"web\s+search\s*",
                    r"search\s+the\s+web\s+for\s+",
                    r"can\s+you\s+search\s+(for\s+)?",
                    r"please\s+search\s+(for\s+)?",
                    r"\.?\s*search\s+web\s*\.?$"
                ]
                
                for pattern in patterns_to_remove:
                    old_query = search_query
                    search_query = re.sub(pattern, "", search_query, flags=re.IGNORECASE).strip()
                    if old_query != search_query and debugging:
                        print(f"   Pattern '{pattern}' removed: '{old_query}' → '{search_query}'")
                
                old_query = search_query
                search_query = re.sub(r'[.!?]+\s*$', '', search_query).strip()
                if old_query != search_query and debugging:
                    print(f"   Punctuation removed: '{old_query}' → '{search_query}'")
                
                if len(search_query) > 2:
                    if debugging:
                        print(f"   Final search query: '{search_query}' (length: {len(search_query)})")
                        print(f"   Calling search tool...")
                    
                    search_result = execute_tool("search_web", {"query": search_query})
                    
                    if isinstance(search_result, dict) and search_result.get("success"):
                        if debugging:
                            print(f"    Search successful! Processing {len(search_result.get('results', []))} results")
                        
                        search_info = f"Based on my web search for '{search_query}', here's what I found:\n\n"
                        
                        if search_result.get("results"):
                            for i, result in enumerate(search_result["results"][:3], 1):
                                title = result.get('title', 'No title')
                                snippet = result.get('snippet', 'No description available')
                                snippet = re.sub(r'<[^>]+>', '', snippet)
                                search_info += f"{i}. **{title}**\n{snippet}\n\n"
                                
                                if debugging:
                                    print(f"     Result {i}: {title[:50]}...")
                        
                        if "Current message:" in full_message:
                            enhanced_message = re.sub(
                                r"(Current message:\s*)(.+?)(\n\n.*)?$", 
                                f"\\1{user_message}\\n\\nSearch results:\\n{search_info}\\n\\nPlease provide a helpful response based on this information.\\3", 
                                full_message, 
                                flags=re.DOTALL
                            )
                        else:
                            enhanced_message = f"User asked: {user_message}\n\nSearch results:\n{search_info}\n\nPlease provide a helpful response based on this information."
                        
                        if debugging:
                            print(f"    Enhanced message created (length: {len(enhanced_message)})")
                        
                        openai_messages[-1]["content"] = enhanced_message
                    else:
                        if debugging:
                            print(f"    Search failed: {search_result.get('error', 'Unknown error')}")
                else:
                    if debugging:
                        print(f"    Search query too short: '{search_query}' (length: {len(search_query)})")
            
            has_math_keywords = any(keyword in user_message_lower for keyword in [
                "calculate", "what is", "solve", "times", "plus", "minus", "divided", "multiply"
            ])
            has_math_symbols = any(symbol in user_message for symbol in ["+", "-", "*", "/", "=", "^"])
            has_numbers = bool(re.search(r'\d', user_message))
            
            if debugging:
                print(f"    Math check: keywords={has_math_keywords}, symbols={has_math_symbols}, numbers={has_numbers}")
            
            if has_math_keywords or (has_math_symbols and has_numbers):
                if debugging:
                    print(f"    CHECKING FOR MATH EXPRESSIONS")
                
                math_patterns = [
                    r"calculate\s+(.+)",
                    r"what\s+is\s+(.+)",
                    r"(\d+[\+\-\*/\^\(\)\s\d\.]+[\d\.]+)\s*[=?]?",
                    r"solve\s+(.+)",
                    r"(\d+)\s+(times|multiplied\s+by|plus|minus|divided\s+by)\s+(\d+)",
                    r"(\d+)\s*[\*\+\-\/\^]\s*(\d+)"
                ]
            
                for i, pattern in enumerate(math_patterns):
                    match = re.search(pattern, user_message_lower)
                    if match:
                        if i == 4:
                            num1, operator, num2 = match.groups()
                            expression = f"{num1} {operator} {num2}"
                            if debugging:
                                print(f"   Pattern {i+1} matched (natural language): '{num1} {operator} {num2}'")
                        else:
                            expression = match.group(1).strip()
                            if debugging:
                                print(f"   Pattern {i+1} matched: '{pattern}' → '{expression}'")
                        
                        original_expression = expression
                        expression = expression.replace("times", "*")
                        expression = expression.replace("multiplied by", "*") 
                        expression = expression.replace("plus", "+")
                        expression = expression.replace("minus", "-")
                        expression = expression.replace("divided by", "/")
                        expression = expression.replace("×", "*")
                        expression = expression.replace("÷", "/")
                        expression = expression.replace("^", "**")
                        
                        if debugging and original_expression != expression:
                            print(f"   Natural language converted: '{original_expression}' → '{expression}'")
                        
                        has_numbers = bool(re.search(r'\d', expression))
                        has_operators = any(op in expression for op in ['+', '-', '*', '/', '**', '(', ')'])
                        is_long_enough = len(expression.replace(' ', '')) > 2
                        
                        if debugging:
                            print(f"   Has numbers: {has_numbers}, Has operators: {has_operators}, Long enough: {is_long_enough}")
                        
                        if has_numbers and (has_operators or "times" in original_expression or "plus" in original_expression):
                            if debugging:
                                print(f"     INITIATING MATH CALCULATION")
                                print(f"   Expression: '{expression}'")
                            
                            math_result = execute_tool("calculate_math", {"expression": expression})
                            
                            if isinstance(math_result, dict) and math_result.get("success"):
                                result_value = math_result.get('result')
                                calc_info = f"\nCalculation result: {original_expression} = {result_value}\n"
                                
                                if debugging:
                                    print(f"    Math calculation successful: {result_value}")
                                
                                original_content = openai_messages[-1]["content"]
                                enhanced_content = f"{original_content}\n{calc_info}\nPlease provide a response that includes this calculation."
                                openai_messages[-1]["content"] = enhanced_content
                            else:
                                if debugging:
                                    print(f"    Math calculation failed: {math_result.get('error', 'Unknown error')}")
                            break
                        elif debugging:
                            print(f"     Expression doesn't qualify as math: '{expression}'")
                else:
                    if debugging:
                        print(f"   No math expressions detected")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": 4000,
            "stream": False
        }
        
        if debugging:
            print(f"   DeepSeek API request: {json.dumps(payload, indent=2)[:500]}...")
        
        base_timeout = 45 if use_tools else 25
        message_length = sum(len(msg["content"]) for msg in openai_messages)
        
        if message_length > 2000:
            timeout = base_timeout + 30
        elif message_length > 1000:
            timeout = base_timeout + 15
        else:
            timeout = base_timeout
            
        timeout = min(timeout, 120)
        
        max_retries = 3
        
        if debugging:
            print(f"   Using timeout: {timeout}s (message length: {message_length} chars)")
        
        for attempt in range(max_retries + 1):
            try:
                if debugging and attempt > 0:
                    print(f"   Retry attempt {attempt + 1}/{max_retries + 1}")
                
                if attempt > 0:
                    import time
                    backoff_time = min(2 ** attempt, 8)  # Max 8 seconds
                    if debugging:
                        print(f"   Waiting {backoff_time}s before retry...")
                    time.sleep(backoff_time)
                
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )
                break
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries:
                    if debugging:
                        print(f"   Timeout/connection error on attempt {attempt + 1}, retrying with longer timeout...")
                    timeout = min(timeout + 20, 150)
                    continue
                else:
                    if debugging:
                        print(f"   All retry attempts failed, using fallback response")
                    return "I'm sorry, but my response is taking longer than expected. This might be due to high server load. Please try asking your question again, or try rephrasing it in a simpler way."
        
        if debugging:
            print(f"   DeepSeek API response status: {response.status_code}")
        
        response.raise_for_status()
        
        result = response.json()
        
        if debugging:
            print(f"   DeepSeek API response: {json.dumps(result, indent=2)[:500]}...")
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise DeepSeekAPIError("No response choices found in API result")
    
    except requests.exceptions.RequestException as e:
        error_msg = f"DeepSeek API request error: {e}"
        print(error_msg)
        if debugging:
            import traceback
            traceback.print_exc()
        raise DeepSeekAPIError(f"DeepSeek API request failed: {str(e)}")
    
    except Exception as e:
        error_msg = f"Error calling DeepSeek API: {e}"
        print(error_msg)
        if debugging:
            import traceback
            traceback.print_exc()
        
        raise DeepSeekAPIError(f"DeepSeek API call failed: {str(e)}")

class DeepSeekAPIError(Exception):
    def __init__(self, message, error_type="api_error"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)