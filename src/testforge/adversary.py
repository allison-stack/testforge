"""
Adversary — generates "bugs that could plausibly exist" for the target

WHAT THIS IS
    A wrapper around mutmut (an off-the-shelf mutation testing tool)

WHY IT MATTERS
    The mutations are the test of your test. If the Author's test passes
    on the original code AND on every mutation, the test is testing
    nothing. The proportion of mutations the test KILLS (i.e., causes to
    fail) is your headline metric: the *mutation kill rate*.

WHY NO LLM IN v0.1
    Mutmut handles ~80% of useful mutation operators for free, with zero
    API spend, instantly, deterministically. Adding an LLM-based Adversary
    that produces "semantic" mutations is a v0.2 feature.
"""

import subprocess
import tempfile
from pathlib import Path


def generate_mutations(target_code: str) -> list[str]:
    """
    Generate mutated versions of the target function.

    Args:
        target_code: Full source of the target function

    Returns:
        List of mutated source strings. Each will be a replacement
        for `target_code`.
    """
    with tempfile.TemporaryDirectory() as d:
        Path(d, "target.py").write_text(target_code, encoding="utf-8")
        Path(d, "pyproject.toml").write_text(
            '[tool.mutmut]\nsource_paths = ["target.py"]\nmutate_only_covered_lines = true',
            encoding="utf-8",
        )
        # generate mutations (test run will fail — that's fine, cache is still written)
        subprocess.run(["python", "-m", "mutmut", "run"], cwd=d, capture_output=True)
        result = subprocess.run(
            ["python", "-m", "mutmut", "results"], cwd=d, capture_output=True, text=True
        )
        ids = result.stdout.strip().splitlines()
        mutations = []
        for mutant_id in ids:
            show = subprocess.run(
                ["python", "-m", "mutmut", "show", mutant_id],
                cwd=d,
                capture_output=True,
                text=True,
            )
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
