"""
Model router — the single place all LLM calls go through.

WHY IT MATTERS
    Every agent (Author, Judge, Supervisor) calls `call_llm`. If you ever
    want to add caching, retries, logging, or swap providers, this is the
    one file you change.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = OpenAI(
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.environ["OPENROUTER_API_KEY"],
)


def call_llm(
    model: str, system: str, user: str, *, temperature: float = 0.2, max_tokens: int = 2000
) -> tuple[str, int]:
    """
    Single LLM call. Returns (text, total_tokens_used)

    Args:
        model: OpenRouter model id (e.g. "openai/gpt-oss-120b:free")
        system: System prompt — the agent's role definition
        user: User message — the actual input for this call
        temperature: 0.0 to 1.0
        max_tokens: Cap on output length

    Returns:
        (output_text, total_tokens) note that `total_tokens` includes both prompt
        and output
    """
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
    tokens = response.usage.total_tokens if response.usage else 0
    return text, tokens
