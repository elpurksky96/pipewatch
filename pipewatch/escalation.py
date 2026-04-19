"""Alert escalation: track consecutive failures and escalate after threshold."""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

DEFAULT_STATE_PATH = Path(".pipewatch_escalation.json")


@dataclass
class EscalationState:
    key: str
    consecutive_failures: int = 0
    last_failure_ts: Optional[float] = None
    escalated: bool = False


def _load_all(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, indent=2))


def load_state(key: str, path: Path = DEFAULT_STATE_PATH) -> EscalationState:
    raw = _load_all(path).get(key)
    if raw is None:
        return EscalationState(key=key)
    return EscalationState(
        key=key,
        consecutive_failures=raw.get("consecutive_failures", 0),
        last_failure_ts=raw.get("last_failure_ts"),
        escalated=raw.get("escalated", False),
    )


def save_state(state: EscalationState, path: Path = DEFAULT_STATE_PATH) -> None:
    data = _load_all(path)
    data[state.key] = {
        "consecutive_failures": state.consecutive_failures,
        "last_failure_ts": state.last_failure_ts,
        "escalated": state.escalated,
    }
    _save_all(data, path)


def record_failure(key: str, path: Path = DEFAULT_STATE_PATH) -> EscalationState:
    state = load_state(key, path)
    state.consecutive_failures += 1
    state.last_failure_ts = time.time()
    save_state(state, path)
    return state


def record_success(key: str, path: Path = DEFAULT_STATE_PATH) -> EscalationState:
    state = load_state(key, path)
    state.consecutive_failures = 0
    state.escalated = False
    state.last_failure_ts = None
    save_state(state, path)
    return state


def should_escalate(state: EscalationState, threshold: int) -> bool:
    """Return True if consecutive failures have reached the threshold."""
    return state.consecutive_failures >= threshold


def mark_escalated(key: str, path: Path = DEFAULT_STATE_PATH) -> EscalationState:
    state = load_state(key, path)
    state.escalated = True
    save_state(state, path)
    return state
