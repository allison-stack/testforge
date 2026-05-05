"""
Model router
- The one place all LLM calls go through

WHY IT MATTERS
- Every agent (Author, Judge, Supervisor) calls `call_llm`
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

# loads environment variables like OpenRouter API key
load_dotenv()

_client = OpenAI(
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.environ["OPENROUTER_API_KEY"],
)


def call_llm(
    model: str, system: str, user: str, *, temperature: float = 0.2, max_tokens: int = 2000
) -> tuple[str, int]:
    """
    A single LLM call

    Args:
        model: OpenRouter model id
        system: System prompt
        user: User message
        temperature: 0.0 to 1.0
        max_tokens: Limit output length

    Returns:
        (output_text, total_tokens)
    """
    # generated response given system and user prompt to the llm
    response = _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    text = response.choices[0].message.content or ""
    # track token usage
    tokens = response.usage.total_tokens if response.usage else 0
    return text, tokens
