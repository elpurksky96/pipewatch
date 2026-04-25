"""Circuit breaker: pause alerting/execution after N consecutive failures."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

DEFAULT_STATE_PATH = Path(".pipewatch") / "circuit_breaker.json"


@dataclass
class CircuitState:
    command: str
    consecutive_failures: int = 0
    tripped_at: Optional[float] = None  # epoch seconds
    reset_after: int = 300  # seconds until auto-reset attempt

    def is_open(self) -> bool:
        """Return True when the circuit is tripped (open = blocking)."""
        if self.tripped_at is None:
            return False
        elapsed = time.time() - self.tripped_at
        return elapsed < self.reset_after

    def is_half_open(self) -> bool:
        """Return True when the cooldown has passed but not yet reset."""
        if self.tripped_at is None:
            return False
        return not self.is_open()


def _load(path: Path) -> Dict[str, dict]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(path: Path, data: Dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def load_state(command: str, path: Path = DEFAULT_STATE_PATH) -> CircuitState:
    raw = _load(path).get(command, {})
    return CircuitState(
        command=command,
        consecutive_failures=raw.get("consecutive_failures", 0),
        tripped_at=raw.get("tripped_at"),
        reset_after=raw.get("reset_after", 300),
    )


def save_state(state: CircuitState, path: Path = DEFAULT_STATE_PATH) -> None:
    data = _load(path)
    data[state.command] = {
        "consecutive_failures": state.consecutive_failures,
        "tripped_at": state.tripped_at,
        "reset_after": state.reset_after,
    }
    _save(path, data)


def record_outcome(
    command: str,
    success: bool,
    threshold: int = 3,
    reset_after: int = 300,
    path: Path = DEFAULT_STATE_PATH,
) -> CircuitState:
    """Update circuit state after a run; trip if threshold reached."""
    state = load_state(command, path)
    state.reset_after = reset_after
    if success:
        state.consecutive_failures = 0
        state.tripped_at = None
    else:
        state.consecutive_failures += 1
        if state.consecutive_failures >= threshold and state.tripped_at is None:
            state.tripped_at = time.time()
    save_state(state, path)
    return state


def reset_circuit(command: str, path: Path = DEFAULT_STATE_PATH) -> None:
    """Manually reset a tripped circuit."""
    state = load_state(command, path)
    state.consecutive_failures = 0
    state.tripped_at = None
    save_state(state, path)
