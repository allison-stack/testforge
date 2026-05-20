"""Tests for the use_judge flag added to run_cycle."""

from unittest.mock import patch

from testforge.orchestrator import run_cycle

SIMPLE_TARGET = "def add(a: int, b: int) -> int:\n    return a + b\n"


def test_use_judge_false_skips_judge_call():
    """When use_judge=False and mutations survive, judge() must not be called."""
    with (
        patch("testforge.orchestrator.judge") as mock_judge,
        patch("testforge.orchestrator.author") as mock_author,
        patch("testforge.orchestrator.run_test") as mock_run,
        patch("testforge.orchestrator.generate_mutations") as mock_mut,
    ):
        mock_author.return_value = ("def test_add():\n    assert True\n", 10)
        mock_run.return_value.passed = True
        # Return a survivor so we'd normally enter the judge branch.
        mock_mut.return_value = ["def add(a, b): return a - b\n"]

        result = run_cycle(SIMPLE_TARGET, target_name="add_nj", use_judge=False)

        assert mock_judge.call_count == 0
        assert result.judge_critique is None
        assert result.stopped_reason == "no_judge"


def test_use_judge_true_still_calls_judge():
    """Regression guard: default behavior must still invoke judge when mutations survive."""
    with (
        patch("testforge.orchestrator.judge") as mock_judge,
        patch("testforge.orchestrator.author") as mock_author,
        patch("testforge.orchestrator.run_test") as mock_run,
        patch("testforge.orchestrator.generate_mutations") as mock_mut,
    ):
        mock_author.return_value = ("def test_add():\n    assert True\n", 10)
        mock_judge.return_value = ("test missed a case", 5)
        mock_run.return_value.passed = True
        # First call: survivor exists → judge runs. Second call: no survivors → break.
        mock_mut.side_effect = [["def add(a, b): return a - b\n"], []]

        run_cycle(SIMPLE_TARGET, target_name="add_yj", use_judge=True)

        assert mock_judge.call_count >= 1


def test_use_llm_adversary_calls_llm_mutations():
    """When use_llm_adversary=True, generate_llm_mutations() is invoked and its
    mutations are unioned with the mutmut mutations."""
    with (
        patch("testforge.orchestrator.author") as mock_author,
        patch("testforge.orchestrator.judge") as mock_judge,
        patch("testforge.orchestrator.run_test") as mock_run,
        patch("testforge.orchestrator.generate_mutations") as mock_mutmut,
        patch("testforge.orchestrator.generate_llm_mutations") as mock_llm_mut,
    ):
        mock_author.return_value = ("def test_add():\n    assert True\n", 10)
        mock_judge.return_value = ("looks fine", 5)
        mock_run.return_value.passed = True
        mock_mutmut.return_value = ["def add(a, b): return a - b\n"]
        mock_llm_mut.return_value = (["def add(a, b): return a * b\n"], 42)

        result = run_cycle(
            SIMPLE_TARGET,
            target_name="add_llm_adv",
            use_llm_adversary=True,
            use_judge=False,  # short-circuit the loop
        )

        assert mock_llm_mut.call_count >= 1
        assert result.mutations_total == 2  # one mutmut + one llm
