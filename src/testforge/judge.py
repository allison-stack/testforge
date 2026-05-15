"""
Judge
- Reviews the Author's test against mutation results

WHY IT MATTERS
- The Judge runs on a different model family than the Author
- Hypothesis to be tested: Same-model judges share blind spots while different-model judges
  catch them
- Ablation experiment:
    - Homogeneous model run: Author=GPT, Judge=GPT
    - Heterogeneous model run: Author=GPT, Judge=Laguna
"""

from pathlib import Path

from .llm import call_llm

_PROMPT_PATH = Path(__file__).parent / "prompts" / "judge.txt"


def judge(
    target_code: str,
    test_code: str,
    surviving_mutations: list[str],
    model: str = "poolside/laguna-m.1:free",
) -> tuple[str, int]:
    """
    Provide critique on a test that failed to catch some mutations

    Args:
        target_code: The original function
        test_code: The Author's test (passes on the target code)
        surviving_mutations: The mutations the test FAILED to catch
        model: OpenRouter model id.

    Returns:
        (critique_text, tokens_used)
    """
    # system prompt
    system_prompt = _PROMPT_PATH.read_text()

    # surviving mutations in a numbered list
    numbered = "\n\n".join(f"Mutation {i + 1}:\n{m}" for i, m in enumerate(surviving_mutations))

    # user prompt
    user_prompt = f"""Target code: {target_code}\n
    Current test: {test_code}\n
    Survivng mutations as a numbered list: {numbered}"""

    # llm generates feedback
    return call_llm(model, system_prompt, user_prompt)
