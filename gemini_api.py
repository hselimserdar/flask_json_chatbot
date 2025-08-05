#gemini_api.py
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import List, Dict, Optional
from tools import AVAILABLE_TOOLS, execute_tool

load_dotenv()
debugging = os.getenv("debugging", "false").lower() == "true"

def call_gemini_api(
    messages: List[Dict[str, str]],
    model: str = "gemini-2.0-flash-exp",
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
        "system": "user",    # Gemini only accepts 'user' or 'model'
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

    # Prepare tools if enabled
    tools = None
    if use_tools:
        tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="search_web",
                        description="Search the web for current information",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "query": types.Schema(
                                    type=types.Type.STRING,
                                    description="The search query"
                                )
                            },
                            required=["query"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="calculate_math",
                        description="Calculate mathematical expressions",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "expression": types.Schema(
                                    type=types.Type.STRING,
                                    description="The mathematical expression to calculate"
                                )
                            },
                            required=["expression"]
                        )
                    )
                ]
            )
        ]

    try:
        # Generate response
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=temperature,
                candidate_count=candidate_count
            ),
            tools=tools
        )
        
        # Handle tool calls
        if response.candidates and response.candidates[0].content.parts:
            final_response = ""
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    final_response += part.text
                elif hasattr(part, 'function_call') and part.function_call:
                    # Execute tool
                    tool_name = part.function_call.name
                    tool_args = dict(part.function_call.args)
                    
                    if debugging:
                        print(f"Tool called: {tool_name} with args: {tool_args}")
                    
                    tool_result = execute_tool(tool_name, tool_args)
                    
                    # Add tool result to conversation and get final response
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part.from_function_response(
                            name=tool_name,
                            response={"result": tool_result}
                        )]
                    ))
                    
                    # Get final response with tool result
                    final_response_obj = client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            temperature=temperature,
                            candidate_count=candidate_count
                        )
                    )
                    
                    final_response += final_response_obj.text
            
            return final_response if final_response else response.text
        
        return response.text
    
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        if debugging:
            import traceback
            traceback.print_exc()
        return "I apologize, but I'm experiencing technical difficulties. Please try again later."
