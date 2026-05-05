"""
Author
- the agent that writes the test case

WHAT THIS IS
- An LLM call that takes the target function code, returns
  pytest test code
"""

import re
from pathlib import Path

from .llm import call_llm

_PROMPT_PATH = Path(__file__).parent / "prompts" / "author.txt"


def author(
    target_code: str, model: str = "openai/gpt-oss-120b:free", critique: str | None = None
) -> tuple[str, int]:
    """
    Generate a pytest test for target_code

    Args:
        target_code: The full source of the function to test
        model: OpenRouter model
        critique: Judge feedback on how to improve test case

    Returns:
        (test_code, tokens_used)
    """
    # system prompt
    system_prompt = _PROMPT_PATH.read_text()

    # user prompt
    user_prompt = f"""Write a single pytest function for the given target code:\n
    {target_code}"""

    # previous test case not good enough as it passed on some mutation
    if critique:
        user_prompt += f"""\n\nThe previous test was weak,
        it passed on some mutation during mutation testing.
        Feedback to improve the test: {critique}"""

    # llm generates test case
    text, tokens = call_llm(model, system_prompt, user_prompt)

    # strip ```python fences from output
    text = re.sub(r"^```python\n|```$", "", text, flags=re.MULTILINE)

    # return generated test case and tokens used
    return text, tokens
