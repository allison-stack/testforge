"""
Adversary — generates "bugs that could plausibly exist" for the target

WHAT THIS IS
    A wrapper around mutmut

WHY IT MATTERS
    The mutations are the test of the test. If the Author's test passes on the original code AND on
    some/every mutation, the test is testing nothing.
    Mutmut handles ~80% of useful mutation operators for free, with zero API spend,
    instantly, deterministically.

FEATURES TO IMPLEMENT IN THE FUTURE
    Adding an LLM-based Adversary that produces "semantic" mutations
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
            '[tool.mutmut]\npaths_to_mutate = ["target.py"]\n',
            encoding="utf-8",
        )
        # generate mutations
        subprocess.run(["python", "-m", "mutmut", "run"], cwd=d, capture_output=True)
        result = subprocess.run(
            ["python", "-m", "mutmut", "results"], cwd=d, capture_output=True, text=True
        )
        ids = [
            line.split(":")[0].strip()
            for line in result.stdout.strip().splitlines()
            if line.strip()
        ]
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
