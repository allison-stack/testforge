"""
Smoke tests for the Executor.

These are tests *of TestForge itself* — not the tests TestForge generates.
Run them with `uv run pytest tests/test_executor.py -m integration -v`.
"""

import pytest

from testforge.executor import run_test


@pytest.mark.integration
def test_executor_passes_a_correct_test() -> None:
    target = "def add(a, b):\n    return a + b\n"
    test = (
        "from target import add\n"
        "def test_add():\n"
        "    assert add(1, 2) == 3\n"
        "    assert add(0, 0) == 0\n"
    )
    result = run_test(target, test)
    assert result.passed, f"expected pass, got:\n{result.stdout}\n{result.stderr}"


@pytest.mark.integration
def test_executor_fails_on_broken_target() -> None:
    target = "def add(a, b):\n    return a - b\n"  # bug
    test = "from target import add\ndef test_add():\n    assert add(1, 2) == 3\n"
    result = run_test(target, test)
    assert not result.passed
