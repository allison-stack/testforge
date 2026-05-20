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
import sys
import tempfile
from pathlib import Path

from openai import APIError

from .llm import call_llm
from .models import ADVERSARY_MODEL

_PROMPT_PATH = Path(__file__).parent / "prompts" / "adversary.txt"
_EXPECTED_LLM_MUTATIONS = 5

# mutmut is deterministic - cache its output per target source so repeated
# calls within a process don't re-spawn the subprocess
_MUTMUT_CACHE: dict[str, list[str]] = {}


def clear_mutation_cache() -> None:
    """Reset the mutmut cache. Useful in tests; not called by production code."""
    _MUTMUT_CACHE.clear()


def _top_level_function_name(code: str) -> str | None:
    """Return the name of the first top-level function defined in `code`, or None."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            return node.name
    return None


def generate_mutations(target_code: str) -> list[str]:
    """
    Generate mutated versions of the target function.

    Results are cached per `target_code` for the lifetime of the process,
    because mutmut is a pure function of its input. Repeated calls with the
    same source string skip the subprocess entirely.

    Args:
        target_code: Full source of the target function

    Returns:
        List of mutated source strings
    """
    if target_code in _MUTMUT_CACHE:
        # shallow-copy so caller mutation can't corrupt the cached entry
        return list(_MUTMUT_CACHE[target_code])

    # create individual temporary environment for mutations
    with tempfile.TemporaryDirectory() as d:
        Path(d, "target.py").write_text(target_code, encoding="utf-8")
        Path(d, "pyproject.toml").write_text(
            '[tool.mutmut]\npaths_to_mutate = ["target.py"]\n',
            encoding="utf-8",
        )
        # run mutmut on target code
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
        _MUTMUT_CACHE[target_code] = mutations
        return list(mutations)


def generate_llm_mutations(target_code: str, model: str = ADVERSARY_MODEL) -> tuple[list[str], int]:
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

    # llm to generates semantic mutations (mutmut handles the syntactic mutations)
    # bump max_tokens — 5 mutations x full function source can exceed the default 2000
    # and truncated blocks (missing ===END===) are silently dropped by the regex below
    # APIError covers rate limits, timeouts, connection failures, and server errors;
    # the LLM adversary is supplemental, so fall back to mutmut-only on failure
    # rather than aborting the whole cycle.
    try:
        text, tokens = call_llm(model, system_prompt, user_prompt, max_tokens=4000)
    except APIError as e:
        print(
            f"[adversary] LLM call failed ({type(e).__name__}: {e}). "
            "Returning 0 mutations; cycle will continue with mutmut only.",
            file=sys.stderr,
        )
        return [], 0

    expected_name = _top_level_function_name(target_code)

    # parse text into a list of mutated source strings
    extracted = re.findall(r"===MUTATION===\s*(.*?)\s*===END===", text, re.DOTALL)
    mutations = []
    for block in extracted:
        block = block.strip()
        # avoid parsing empty or repeat mutations
        if not block or block == target_code.strip() or block in mutations:
            continue
        try:
            tree = ast.parse(block)
        # avoid adding mutations with syntax errors to mutations list
        except SyntaxError:
            continue
        # the executor imports the mutated function by its original name; if the LLM
        # renamed it (or wrapped it in something else), the import fails and pytest
        # exits nonzero — which would be falsely scored as a kill. drop these.
        if expected_name is not None:
            has_match = any(
                isinstance(n, ast.FunctionDef) and n.name == expected_name for n in tree.body
            )
            if not has_match:
                continue
        mutations.append(block)

    if len(mutations) < _EXPECTED_LLM_MUTATIONS:
        print(
            f"[adversary] warning: expected {_EXPECTED_LLM_MUTATIONS} mutations, "
            f"got {len(mutations)} (extracted={len(extracted)}). "
            "Likely truncation or post-parse filtering.",
            file=sys.stderr,
        )
    return mutations, tokens
