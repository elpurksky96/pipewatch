"""Hooks that integrate circuit breaker logic into the run lifecycle."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pipewatch.circuit_breaker import (
    DEFAULT_STATE_PATH,
    CircuitState,
    load_state,
    record_outcome,
)
from pipewatch.watcher import WatchResult


def evaluate_circuit(
    command: str,
    result: WatchResult,
    threshold: int = 3,
    reset_after: int = 300,
    path: Path = DEFAULT_STATE_PATH,
) -> CircuitState:
    """Record run outcome and return updated circuit state."""
    run_ok = result.run_result.success if result.run_result else False
    return record_outcome(
        command=command,
        success=run_ok,
        threshold=threshold,
        reset_after=reset_after,
        path=path,
    )


def should_skip_due_to_circuit(
    command: str,
    path: Path = DEFAULT_STATE_PATH,
) -> bool:
    """Return True if the circuit is open and the run should be skipped."""
    state = load_state(command, path)
    return state.is_open()


def print_circuit_notice(state: CircuitState) -> None:
    if state.is_open():
        print(
            f"[circuit-breaker] OPEN — '{state.command}' has "
            f"{state.consecutive_failures} consecutive failure(s). "
            f"Execution blocked until cooldown expires."
        )
    elif state.is_half_open():
        print(
            f"[circuit-breaker] HALF-OPEN — '{state.command}' cooldown elapsed; "
            "next run will attempt recovery."
        )
    elif state.consecutive_failures > 0:
        print(
            f"[circuit-breaker] CLOSED — '{state.command}' "
            f"({state.consecutive_failures} failure(s) recorded, not yet tripped)."
        )
