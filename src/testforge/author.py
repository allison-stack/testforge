"""Author — the agent that writes the candidate test.

WHAT THIS IS
    An LLM call. That's it. Takes the target function code, returns
    pytest test code as a string.

WHY IT MATTERS
    The Author is your "creative" step. Its quality sets the ceiling for
    everything downstream — the Judge can only improve a test, not invent
    one from scratch. Iterating on the Author prompt is where most of
    your week 2 time goes. *That iteration is the actual AI engineering
    in this project.*

WHAT YOU'LL WRITE
    - The system prompt in `prompts/author.txt` (most important file in
      the repo — write 3+ versions and save them all).
    - This thin function below that loads the prompt and calls the model.

PROMPT-DESIGN HINTS (LEARN THESE THE HARD WAY)
    - "Return ONLY Python code, no markdown" or you'll spend a day
      stripping ```python fences.
    - "Use at least 3 assert statements with different inputs" or the
      model writes `assert add(1,2) == 3` and calls it done.
    - One concrete example in the system prompt is worth a paragraph of
      instructions.
"""

import re
from pathlib import Path

from .llm import call_llm

_PROMPT_PATH = Path(__file__).parent / "prompts" / "author.txt"


def author(target_code: str, model: str = "openai/gpt-oss-120b:free") -> tuple[str, int]:
    """
    Generate a pytest test for `target_code`.

    Args:
        target_code: The full source of the function to test.
        model: OpenRouter model id.

    Returns:
        (test_code, tokens_used)
    """
    # 1. system_prompt = _PROMPT_PATH.read_text()
    system_prompt = _PROMPT_PATH.read_text()
    # 2. user_msg = f"Write a single pytest function for:\n\n{target_code}"
    user_prompt = f"""Write a pytest test for the given target code:\n
    {target_code}"""
    # 3. text, tokens = call_llm(model, system_prompt, user_msg)
    text, tokens = call_llm(model, system_prompt, user_prompt)
    # 4. strip ```python fences from text if present
    text = re.sub(r"^```python\n|```$", "", text, flags=re.MULTILINE)
    # 5. return text, tokens
    return text, tokens
