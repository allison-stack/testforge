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
from .models import AUTHOR_MODEL

_PROMPT_PATH = Path(__file__).parent / "prompts" / "author.txt"


def author(
    target_code: str,
    model: str = AUTHOR_MODEL,
    critique: str | None = None,
    *,
    previous_test: str | None = None,
    surviving_mutations: list[str] | None = None,
) -> tuple[str, int]:
    """
    Generate a pytest test for target_code

    Args:
        target_code: The full source of the function to test
        model: OpenRouter model
        critique: Judge feedback on how to improve test case
        previous_test: The author's prior test (used as the anchor on retries so
            the author augments existing assertions instead of rewriting).
        surviving_mutations: Full source of each mutation the prior test failed
            to detect, so the author can pick distinguishing inputs directly
            rather than relying on the judge's prose alone.

    Returns:
        (test_code, tokens_used)
    """
    # system prompt
    system_prompt = _PROMPT_PATH.read_text()

    # user prompt
    user_prompt = f"""Write a single pytest function for the given target code:\n
    {target_code}"""

    if previous_test is not None:
        # retry with full iteration context — author should augment, not rewrite
        user_prompt += (
            "\n\nITERATION CONTEXT (this is a retry)\n"
            "Your previous test passed on the original but missed some mutations.\n\n"
            "PREVIOUS TEST (preserve every assertion, ADD new ones — do NOT rewrite):\n"
            f"{previous_test}\n"
        )
        if surviving_mutations:
            # cap to bound prompt size — in practice 1-3 survive on healthy targets
            shown = surviving_mutations[:10]
            numbered = "\n\n".join(f"Mutation {i + 1}:\n{m}" for i, m in enumerate(shown))
            user_prompt += (
                f"\nSURVIVING MUTATIONS (the previous test FAILED to detect these):\n{numbered}\n"
            )
        if critique:
            user_prompt += f"\nJUDGE FEEDBACK: {critique}\n"
    elif critique:
        # legacy path: critique but no previous_test (e.g., initial_test_failed retry)
        user_prompt += (
            "\n\nThe previous test was weak, it passed on some mutation during mutation testing. "
            f"Feedback to improve the test: {critique}"
        )

    # llm generates test case
    text, tokens = call_llm(model, system_prompt, user_prompt)

    # strip ```python fences from output
    text = re.sub(r"^```python\n|```$", "", text, flags=re.MULTILINE)

    # return generated test case and tokens used
    return text, tokens
