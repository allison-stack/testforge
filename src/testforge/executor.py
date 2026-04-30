"""
Executor — the deterministic ground truth of the system

WHAT THIS IS
    A function that takes target code + test code, runs the test inside
    a Docker container, and returns pass/fail. NOT an LLM. This is the
    most important component in TestForge — every quality claim the system
    makes ultimately bottoms out here.

WHY IT MATTERS
    LLMs lie. They will tell you a test "passes" when it doesn't.
    `pytest` cannot lie. Mixing deterministic verification into the
    pipeline is what separates this project from "a chatbot that writes
    tests."

WHY DOCKER
    Generated test code is *untrusted input*. Running `pytest` on raw LLM
    output on your laptop is how you accidentally `rm -rf` your home dir
    when the model hallucinates a fixture. Docker is your firewall.

DEBUGGING
    - Print the temp dir path during dev — you can `cd` in and run pytest
      manually if a test fails mysteriously.
    - `--rm` on docker run cleans up containers automatically.
    - `-v $tempdir:/work` mounts the host folder into the container.
"""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExecutorResult:
    """Structured result from one pytest run.

    Attributes:
        passed: True iff pytest exit code == 0.
        stdout: Full pytest stdout (useful for the Judge to see WHY a test failed).
        stderr: Full stderr (often where syntax errors show up).
        timed_out: True if we hit the wall-clock limit.
    """

    passed: bool
    stdout: str
    stderr: str
    timed_out: bool


def run_test(
    actual_code: str, test_code: str, *, image: str = "testforge-sandbox", timeout_seconds: int = 60
) -> ExecutorResult:
    """
    Run tests against some target code in docker sandbox
    """
    with tempfile.TemporaryDirectory() as d:
        Path(d, "target.py").write_text(actual_code, encoding="utf-8")
        Path(d, "test_target.py").write_text(test_code, encoding="utf-8")
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", "-v", f"{d}:/work", "-w", "/work", image, "pytest", "-q"],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            return ExecutorResult(
                passed=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as e:
            return ExecutorResult(
                passed=False,
                stdout=str(e.stdout) or "",
                stderr=str(e.stderr) or "",
                timed_out=True,
            )
