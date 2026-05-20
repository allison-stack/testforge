"""
Supervisor
- Guardrail that prevents infinite loops

WHAT THIS IS
- Tracks token usage and retries across a single test cycle and tells the orchestrator when to stop

FEATURES TO IMPLEMENT IN THE FUTURE
    Adding LLM-based replanning
"""

import time
from dataclasses import dataclass, field


@dataclass
class Supervisor:
    """Budget tracker for one cycle through the agent pipeline"""

    max_retries: int = 2
    max_tokens: int = 20_000
    max_seconds: int = 600

    tokens_used: int = 0
    retry_count: int = 0
    start_time: float = field(default_factory=time.time)

    # track tokens
    def record_tokens(self, n: int) -> None:
        self.tokens_used += n

    # retry count
    def record_retry(self) -> None:
        self.retry_count += 1

    # stop Orchestrator loop
    def should_stop(self) -> str | None:
        """
        Return a reason string if there is a reason to stop (None by default)
        """
        if self.retry_count >= self.max_retries:
            return "max_retries"
        if self.tokens_used >= self.max_tokens:
            return "token_budget"
        if time.time() - self.start_time >= self.max_seconds:
            return "timeout"
        return None
