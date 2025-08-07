
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import List, Dict, Optional
from tools import AVAILABLE_TOOLS, execute_tool

load_dotenv()
debugging = os.getenv("debugging", "false").lower() == "true"

def call_gemini_api(
    messages: List[Dict[str, str]],
    model: str = "gemini-2.0-flash-lite",
    temperature: float = 0.3,
    candidate_count: int = 1,
    use_tools: bool = False
) -> str:
    """
    Send a multi-turn chat to Gemini via the official SDK and return the assistant's reply.
    Maps all assistant/bot roles to 'model' to satisfy Gemini's valid-role requirement.
    Supports tool calling for web search and math calculations.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    client = genai.Client(api_key=api_key)

    role_map = {
        "user": "user",
        "system": "user",
        "assistant": "model",
        "bot": "model"
    }

    contents: list[types.Content] = []
    for m in messages:
        role = role_map.get(m["author"], "user")
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=m["content"])]
            )
        )

    try:

        enhanced_response = ""
        
        if use_tools and contents:
            if debugging:
                print(f" GEMINI API DEBUG - Tool processing enabled")
            
            full_message = contents[-1].parts[0].text
            
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
                "find", "currency rate", "search", "on web", "search meaning",
                "find meaning", "what does", "meaning of", "whats"
            ]
            
            found_keywords = [kw for kw in search_keywords if kw in user_message_lower]
            should_search = len(found_keywords) > 0
            
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
                        
                        contents[-1] = types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=enhanced_message)]
                        )
                    else:
                        if debugging:
                            print(f"    Search failed: {search_result.get('error', 'Unknown error')}")
                else:
                    if debugging:
                        print(f"    Search query too short: '{search_query}' (length: {len(search_query)})")
            
            math_patterns = [
                r"calculate\s+(.+)",
                r"what\s+is\s+(.+)",
                r"(\d+[\+\-\*/\^\(\)\s\d\.timesplusmultiplidivideby]+[\d\.]+)\s*[=?]?",
                r"solve\s+(.+)",
                r"(\d+)\s+(times|multiplied\s+by|plus|minus|divided\s+by)\s+(\d+)",
                r"(\d+)\s*[\*\+\-\/\^]\s*(\d+)"
            ]
            
            if debugging:
                print(f"    CHECKING FOR MATH EXPRESSIONS")
            
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
                            
                            original_content = contents[-1].parts[0].text
                            enhanced_content = f"{original_content}\n{calc_info}\nPlease provide a response that includes this calculation."
                            contents[-1] = types.Content(
                                role="user",
                                parts=[types.Part.from_text(text=enhanced_content)]
                            )
                        else:
                            if debugging:
                                print(f"    Math calculation failed: {math_result.get('error', 'Unknown error')}")
                        break
                    elif debugging:
                        print(f"     Expression doesn't qualify as math: '{expression}'")
            else:
                if debugging:
                    print(f"   No math expressions detected")

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=temperature,
                candidate_count=candidate_count
            )
        )
        
        return response.text
    
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        if debugging:
            import traceback
            traceback.print_exc()
        return "I apologize, but I'm experiencing technical difficulties. Please try again later."
