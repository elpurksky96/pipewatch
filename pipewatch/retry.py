"""Retry logic for pipewatch commands."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from pipewatch.runner import RunResult, run_command


@dataclass
class RetryConfig:
    max_attempts: int = 3
    delay_seconds: float = 2.0
    backoff_factor: float = 1.0  # multiplied each attempt


@dataclass
class RetryResult:
    final: RunResult
    attempts: int
    all_results: list[RunResult] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.final.exit_code == 0


def run_with_retry(
    command: str,
    config: RetryConfig,
    timeout: Optional[float] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> RetryResult:
    """Run a command, retrying on failure up to max_attempts times."""
    results: list[RunResult] = []
    delay = config.delay_seconds

    for attempt in range(1, config.max_attempts + 1):
        result = run_command(command, timeout=timeout)
        results.append(result)

        if result.exit_code == 0 or result.timed_out:
            return RetryResult(final=result, attempts=attempt, all_results=results)

        if attempt < config.max_attempts:
            sleep_fn(delay)
            delay *= config.backoff_factor

    return RetryResult(final=results[-1], attempts=len(results), all_results=results)
