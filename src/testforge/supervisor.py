"""
Supervisor — the budget guard that prevents runaway loops

WHAT THIS IS
    Tracks token usage and retries across a single test cycle. Tells the orchestrator when to stop.

WHY IT MATTERS
    Without budgets, an LLM will retry forever on impossible tasks and consume too many tokens.
    The Supervisor acts as the guardrail.

FEATURES TO IMPLEMENT IN THE FUTURE
    Adding LLM-based replanning
"""

import time
from dataclasses import dataclass, field


@dataclass
class Supervisor:
    """Budget tracker for one cycle through the agent pipeline.

    Args:
        max_retries: Max times the Author/Judge feedback loop can iterate.
        max_tokens: Hard cap on total tokens (sum across all agent calls).
        max_seconds: Wall-clock cap. Generous default — set lower for demos.
    """

    max_retries: int = 2
    max_tokens: int = 20_000
    max_seconds: int = 120

    tokens_used: int = 0
    retry_count: int = 0
    start_time: float = field(default_factory=time.time)

    def record_tokens(self, n: int) -> None:
        self.tokens_used += n

    def record_retry(self) -> None:
        self.retry_count += 1

    def should_stop(self) -> str | None:
        """Return a reason string if we should stop, else None."""
        if self.retry_count >= self.max_retries:
            return "max_retries"
        if self.tokens_used >= self.max_tokens:
            return "token_budget"
        if time.time() - self.start_time >= self.max_seconds:
            return "wall_clock"
        return None
