"""Tests for orchestrator flag behavior: iterate, use_llm_adversary."""

from unittest.mock import patch

from testforge.orchestrator import run_cycle

SIMPLE_TARGET = "def add(a: int, b: int) -> int:\n    return a + b\n"


def _executor_returns_passed(mock_session_cls, passed: bool = True) -> None:
    mock_exec = mock_session_cls.return_value.__enter__.return_value
    mock_exec.run.return_value.passed = passed


def test_iterate_false_skips_judge_call():
    with (
        patch("testforge.orchestrator.judge") as mock_judge,
        patch("testforge.orchestrator.author") as mock_author,
        patch("testforge.orchestrator.ExecutorSession") as mock_session,
        patch("testforge.orchestrator.generate_mutations") as mock_mut,
    ):
        mock_author.return_value = ("def test_add():\n    assert True\n", 10)
        _executor_returns_passed(mock_session)
        mock_mut.return_value = ["def add(a, b): return a - b\n"]

        result = run_cycle(SIMPLE_TARGET, target_name="add_baseline", iterate=False)

        assert mock_judge.call_count == 0
        assert result.judge_critique is None
        assert result.stopped_reason == "baseline"


def test_iterate_true_calls_judge_on_survivors():
    with (
        patch("testforge.orchestrator.judge") as mock_judge,
        patch("testforge.orchestrator.author") as mock_author,
        patch("testforge.orchestrator.ExecutorSession") as mock_session,
        patch("testforge.orchestrator.generate_mutations") as mock_mut,
    ):
        mock_author.return_value = ("def test_add():\n    assert True\n", 10)
        mock_judge.return_value = ("test missed a case", 5)
        _executor_returns_passed(mock_session)
        # iter 1: one survivor -> judge runs. iter 2: no mutations -> break.
        mock_mut.side_effect = [["def add(a, b): return a - b\n"], []]

        run_cycle(SIMPLE_TARGET, target_name="add_iterate", iterate=True)

        assert mock_judge.call_count >= 1


def test_use_llm_adversary_unions_mutations():
    with (
        patch("testforge.orchestrator.author") as mock_author,
        patch("testforge.orchestrator.judge") as mock_judge,
        patch("testforge.orchestrator.ExecutorSession") as mock_session,
        patch("testforge.orchestrator.generate_mutations") as mock_mutmut,
        patch("testforge.orchestrator.generate_llm_mutations") as mock_llm_mut,
    ):
        mock_author.return_value = ("def test_add():\n    assert True\n", 10)
        mock_judge.return_value = ("looks fine", 5)
        _executor_returns_passed(mock_session)
        mock_mutmut.return_value = ["def add(a, b): return a - b\n"]
        mock_llm_mut.return_value = (["def add(a, b): return a * b\n"], 42)

        result = run_cycle(
            SIMPLE_TARGET,
            target_name="add_llm_adv",
            use_llm_adversary=True,
            iterate=False,
        )

        assert mock_llm_mut.call_count >= 1
        assert result.mutations_total == 2
