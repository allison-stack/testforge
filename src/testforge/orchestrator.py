"""
Orchestrator
- Calls each agent in order

THE FLOW (one cycle)
1. Author writes a test for the target code
2. Executor runs Author's test on the original target
3. Adversary generates mutations
4. Executor runs the test against each mutation. Mutations the test FAILS on are "killed"
   and the rest are "survived".
5. If any mutations have survived and token limit not reached yet:
   Judge critiques the test and loop back to step 1, otherwise, return the result
6. Supervisor watches budgets the whole time and can break out of the loop if conditions are met
   (like token limit reached)
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adversary import generate_llm_mutations, generate_mutations
from .author import author
from .executor import ExecutorSession
from .judge import judge
from .models import ADVERSARY_MODEL, AUTHOR_MODEL, JUDGE_MODEL
from .supervisor import Supervisor

TRACES_DIR = Path(__file__).resolve().parents[2] / "traces"


@dataclass
class CycleResult:
    """Final report from one orchestration cycle."""

    target_name: str
    test_code: str
    mutations_total: int
    mutations_killed: int
    kill_rate: float
    surviving_mutations: list[str]
    judge_critique: str | None
    stopped_reason: str | None
    tokens_used: int
    retries: int


def run_cycle(
    target_code: str,
    target_name: str,
    *,
    author_model: str = AUTHOR_MODEL,
    judge_model: str = JUDGE_MODEL,
    use_llm_adversary: bool = False,
    adversary_model: str = ADVERSARY_MODEL,
    iterate: bool = True,
    on_iteration: Callable[[dict[str, Any]], None] | None = None,
) -> CycleResult:
    """
    Runs a full cycle on a single target function

    Args:
        target_code: The original function
        target_name: Name of function in target_code
        author_model: Author llm
        judge_model: Judge llm

    Returns:
        (critique_text, tokens_used)
    """

    supervisor = Supervisor()
    tokens_used = 0
    last_critique = None
    # prior iteration's test + survivors, passed to the author on retries so it
    # augments the existing test instead of rewriting from scratch
    last_test_code: str | None = None
    last_surviving_mutations: list[str] | None = None
    # best mutation pass observed so far; preserved across iterations so a later
    # iteration that produces a worse (or broken) test cannot regress the result
    best: dict[str, Any] | None = None

    # one Docker container for the whole cycle - amortizes startup over
    # the test-on-original call plus N mutation runs per iteration
    with ExecutorSession() as executor:
        while True:
            # Author creates pytest for target code
            test_code, tokens = author(
                target_code,
                author_model,
                last_critique,
                previous_test=last_test_code,
                surviving_mutations=last_surviving_mutations,
            )
            tokens_used += tokens
            supervisor.record_tokens(tokens)

            # run test created by author
            result = executor.run(target_code, test_code)
            if not result.passed:
                failure_trace = {
                    "target_name": target_name,
                    "phase": "initial_test_failed",
                    "test_code": test_code,
                    "pytest_stdout": result.stdout,
                    "pytest_stderr": result.stderr,
                    "tokens_used": tokens_used,
                    "retries": supervisor.retry_count,
                }
                write_trace(target_name, failure_trace)
                if on_iteration is not None:
                    on_iteration(failure_trace)
                # baseline mode does not retry the author; supervisor budgets still apply
                if not iterate or supervisor.should_stop():
                    # if any earlier iteration succeeded, prefer its result over
                    # the 0/0 catastrophe of the current failed attempt
                    if best is not None:
                        return CycleResult(
                            target_name=target_name,
                            test_code=best["test_code"],
                            mutations_total=best["mutations_total"],
                            mutations_killed=best["mutations_killed"],
                            kill_rate=best["kill_rate"],
                            surviving_mutations=best["surviving_mutations"],
                            judge_critique=best["critique_used"],
                            stopped_reason="initial_test_failed",
                            tokens_used=tokens_used,
                            retries=supervisor.retry_count,
                        )
                    return CycleResult(
                        target_name=target_name,
                        test_code=test_code,
                        mutations_total=0,
                        mutations_killed=0,
                        kill_rate=0.0,
                        surviving_mutations=[],
                        judge_critique=None,
                        stopped_reason="initial_test_failed",
                        tokens_used=tokens_used,
                        retries=supervisor.retry_count,
                    )
                last_critique = (
                    "The generated test failed to run against the original (unmutated target). "
                    "Pytest output:\n"
                    f"stdout:\n{result.stdout}\n"
                    f"stderr:\n{result.stderr}"
                )
                supervisor.record_retry()
                continue
            else:
                # Adversary generates mutations in target code
                mutations = generate_mutations(target_code)
                llm_mutations: list[str] = []
                if use_llm_adversary:
                    llm_mutations, llm_tokens = generate_llm_mutations(
                        target_code, model=adversary_model
                    )
                    tokens_used += llm_tokens
                    supervisor.record_tokens(llm_tokens)
                    mutations = mutations + llm_mutations
                mutations_killed = 0
                surviving_mutations = []
                # run the original tests generated by Author on mutated target code
                for m in mutations:
                    mut_result = executor.run(m, test_code)
                    if not mut_result.passed:
                        mutations_killed += 1
                    else:
                        surviving_mutations.append(m)

                # see if the tests generated by author fail on mutated code
                kill_rate = mutations_killed / len(mutations) if mutations else 0.0

                trace = {
                    "target_name": target_name,
                    "phase": "mutation_pass",
                    "test_code": test_code,
                    "mutations_total": len(mutations),
                    "mutations_mutmut": len(mutations) - len(llm_mutations),
                    "mutations_llm": len(llm_mutations),
                    "mutations_killed": mutations_killed,
                    "kill_rate": kill_rate,
                    "tokens_used": tokens_used,
                    "retries": supervisor.retry_count,
                }
                # write result trace to log
                write_trace(target_name, trace)
                if on_iteration is not None:
                    on_iteration(trace)

                # snapshot the best iteration; strict > means earlier iters win
                # on ties (LLM adversary mutation count varies between calls)
                if best is None or kill_rate > best["kill_rate"]:
                    best = {
                        "test_code": test_code,
                        "mutations_total": len(mutations),
                        "mutations_killed": mutations_killed,
                        "kill_rate": kill_rate,
                        "surviving_mutations": list(surviving_mutations),
                        "critique_used": last_critique,
                        "iteration": supervisor.retry_count,
                    }

                # stop if all mutations killed
                if not surviving_mutations:
                    stopped_reason = None
                    break

                # baseline mode: one author pass, no judge feedback loop
                if not iterate:
                    stopped_reason = "baseline"
                    break

                # stop if supervisor gives another reason to stop
                # (e.g, run out of tokens allocated for experiment)
                stop = supervisor.should_stop()
                if stop:
                    stopped_reason = stop
                    break

                # Judge provides feedback on the test case that passed on mutation
                critique, c_tokens = judge(target_code, test_code, surviving_mutations, judge_model)
                supervisor.record_tokens(c_tokens)
                supervisor.record_retry()
                tokens_used += c_tokens
                last_critique = critique
                # carry the current test + survivors forward so next iter's
                # author call can augment instead of rewriting from scratch
                last_test_code = test_code
                last_surviving_mutations = surviving_mutations

    # return the best iteration observed across the whole cycle
    if best is not None:
        return CycleResult(
            target_name=target_name,
            test_code=best["test_code"],
            mutations_total=best["mutations_total"],
            mutations_killed=best["mutations_killed"],
            kill_rate=best["kill_rate"],
            surviving_mutations=best["surviving_mutations"],
            judge_critique=best["critique_used"],
            stopped_reason=stopped_reason,
            tokens_used=tokens_used,
            retries=supervisor.retry_count,
        )


# writes a trace log (useful for debugging)
def write_trace(target_name: str, trace: dict[str, Any]) -> None:
    """
    Append-only trace log (aka a compliance audit trail)

    Args:
        target_name: Name of function in target_code
        trace: log

    Returns:
        None
    """
    # create /traces directory
    TRACES_DIR.mkdir(exist_ok=True)
    path = TRACES_DIR / f"{target_name}.jsonl"
    with path.open("a") as f:
        f.write(json.dumps(trace, default=str) + "\n")
