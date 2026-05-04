"""
Judge — reviews the Author's test against mutation results

WHY IT MATTERS
    The Judge runs on a *different model family* than the Author — Author is GPT, Judge is Laguna.
    Same-model judges share blind spots; different-model judges catch them.

    Ablation experiment compares:
        Homogeneous: Author=GPT, Judge=GPT   ← shared blind spots
        Heterogeneous: Author=GPT, Judge=Laguna ← different blind spots
    Expect: heterogeneous to win
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
    Critique a test that failed to catch some mutations.

    Args:
        target_code: The original function
        test_code: The Author's test (which passed on the original)
        surviving_mutations: The mutations the test FAILED to catch
        model: OpenRouter model id. Pick a different family than Author

    Returns:
        (critique_text, tokens_used)
    """
    system_prompt = _PROMPT_PATH.read_text()
    numbered = "\n\n".join(f"Mutation {i + 1}:\n{m}" for i, m in enumerate(surviving_mutations))
    user_prompt = f"""Target code: {target_code}\n
    Current test: {test_code}\n
    Survivng mutations as a numbered list: {numbered}"""
    return call_llm(model, system_prompt, user_prompt)
