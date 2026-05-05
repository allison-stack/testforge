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


def author(
    target_code: str, model: str = "openai/gpt-oss-120b:free", critique: str | None = None
) -> tuple[str, int]:
    """
    Generate a pytest test for `target_code`.

    Args:
        target_code: The full source of the function to test.
        model: OpenRouter model id.

    Returns:
        (test_code, tokens_used)
    """
    # system prompt
    system_prompt = _PROMPT_PATH.read_text()

    # user prompt
    user_prompt = f"""Write a single pytest function for the given target code:\n
    {target_code}"""

    # previous test case not good enough, mutations have survived
    if critique:
        user_prompt += f"""\n\nThe previous test was not robust enough.
        The test passed on some mutation.
        Use this feedback to improve the test:\n{critique}"""

    # let GPT generate test case
    text, tokens = call_llm(model, system_prompt, user_prompt)

    # strip ```python fences from output
    text = re.sub(r"^```python\n|```$", "", text, flags=re.MULTILINE)

    # return generated test case and tokens used
    return text, tokens
