import os
from google import genai
from google.genai import types

# 1) Install the SDK: pip install google-genai
# 2) Configure your API key (or use GOOGLE_API_KEY env var)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
client = genai.Client()

def call_gemini_api(
    messages: list[dict[str, str]],
    model: str = "gemini-2.5-pro",
    temperature: float = 0.3,
    candidate_count: int = 1
) -> str:
    """
    Send a multi-turn chat to Gemini via the Google Gen AI SDK.

    Parameters:
      - messages: List of {"author": "user"|"bot", "content": str}
      - model:       Gemini model code (default "gemini-2.5-pro", free tier)
      - temperature: Sampling temperature (0.0–1.0)
      - candidate_count: How many reply variants to request

    Returns:
      - The assistant’s reply (first candidate) as plain text.
    """
    # Convert your message history into the SDK's Content type
    contents: list[types.Content] = []
    for m in messages:
        contents.append(
            types.Content(
                role=m["author"],
                parts=[types.Part.from_text(text=m["content"])]
            )
        )

    # Call the model, feeding in the entire conversation as "contents"
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=temperature,
            candidate_count=candidate_count
        )
    )
    return response.text
