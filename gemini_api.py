#gemini_api.py
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import List, Dict

load_dotenv()

def call_gemini_api(
    messages: List[Dict[str, str]],
    model: str = "gemini-2.0-flash-lite",
    temperature: float = 0.3,
    candidate_count: int = 1
) -> str:
    """
    Send a multi-turn chat to Gemini via the official SDK and return the assistant’s reply.
    Maps all assistant/bot roles to 'model' to satisfy Gemini's valid-role requirement.
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

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=temperature,
            candidate_count=candidate_count
        )
    )
    return response.text
