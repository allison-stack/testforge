"""
Adversary
- Generates bugs that could plausibly exist (e.g., due to human error) for the target

WHY IT MATTERS
- The mutations are the test of the test
- If the Author's test passes on the original code and on
  some mutation, the test is not good
- Mutmut handles ~80% of useful mutation operators for free,
  and deterministically

FEATURES TO IMPLEMENT
- Adding an LLM-based Adversary that produces "semantic" mutations
"""

import ast
import re
import subprocess
import tempfile
from pathlib import Path

from .llm import call_llm

_PROMPT_PATH = Path(__file__).parent / "prompts" / "adversary.txt"


def generate_mutations(target_code: str) -> list[str]:
    """
    Generate mutated versions of the target function

    Args:
        target_code: Full source of the target function

    Returns:
        List of mutated source strings
    """
    # create individual temporary environment for mutations
    with tempfile.TemporaryDirectory() as d:
        Path(d, "target.py").write_text(target_code, encoding="utf-8")
        Path(d, "pyproject.toml").write_text(
            '[tool.mutmut]\npaths_to_mutate = ["target.py"]\n',
            encoding="utf-8",
        )
        # run mutmut
        subprocess.run(["python", "-m", "mutmut", "run"], cwd=d, capture_output=True)
        result = subprocess.run(
            ["python", "-m", "mutmut", "results"], cwd=d, capture_output=True, text=True
        )
        # store ids of all generated mutations
        ids = [
            line.split(":")[0].strip()
            for line in result.stdout.strip().splitlines()
            if line.strip()
        ]
        mutations = []
        for mutant_id in ids:
            # get diff for each mutation
            show = subprocess.run(
                ["python", "-m", "mutmut", "show", mutant_id],
                cwd=d,
                capture_output=True,
                text=True,
            )
            # get full mutated source string
            patched = subprocess.run(
                ["patch", "-o", "-", "target.py"],
                input=show.stdout,
                cwd=d,
                capture_output=True,
                text=True,
            )
            mutated = patched.stdout
            if mutated:
                mutations.append(mutated)
        return mutations


def generate_llm_mutations(
    target_code: str, model: str = "openai/gpt-oss-120b:free"
) -> tuple[list[str], int]:
    """
    Generate semantic mutations using an LLM adversary.

    Args:
        target_code: Full source of the target function
        model: OpenRouter model

    Returns:
        (list of mutated source strings, tokens_used)
    """
    # system prompt
    system_prompt = _PROMPT_PATH.read_text()

    # user prompt
    user_prompt = (
        "Generate mutations as complete, runnable functions "
        f"for the following code:\n\n{target_code}"
    )

    # call model to generate mutations
    text, tokens = call_llm(model, system_prompt, user_prompt)

    # parse text into a list of mutated source strings
    extracted = re.findall(r"===MUTATION===\s*(.*?)\s*===END===", text, re.DOTALL)
    mutations = []
    for block in extracted:
        block = block.strip()
        if not block or block == target_code.strip() or block in mutations:
            continue
        try:
            ast.parse(block)
        except SyntaxError:
            continue
        mutations.append(block)
    return mutations, tokens
