import os
import requests
from typing import List, Dict, Any

def call_gemini_api(
    messages: List[Dict[str, str]],
    model: str = "gemini-2.5-pro",
    temperature: float = 0.3,
    candidate_count: int = 1,
    timeout: float = 30.0
) -> str:
    """
    Send a multi-turn chat to the Gemini API and return the assistant’s reply.

    Parameters:
      - messages: List of dicts, each with:
          • "author": "system", "user", or "assistant"
          • "content": the text string
      - model:            the Gemini model code (default "gemini-2.5-pro", free tier)
      - temperature:      sampling temperature
      - candidate_count:  number of reply candidates to request
      - timeout:          HTTP request timeout in seconds

    Returns:
      - str: the content of the first reply candidate
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    url = "https://gemini.googleapis.com/v1/chat:generateMessage"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    body: Dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "candidateCount": candidate_count,
        "messages": messages
    }

    response = requests.post(url, json=body, headers=headers, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("No reply candidates returned from Gemini API")

    return candidates[0].get("content", "")
