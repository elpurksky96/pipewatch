"""Alert throttling: suppress duplicate alerts within a cooldown window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

DEFAULT_COOLDOWN = 3600  # seconds


@dataclass
class ThrottleState:
    last_alert: Dict[str, float]


def _load_state(path: Path) -> ThrottleState:
    if not path.exists():
        return ThrottleState(last_alert={})
    try:
        data = json.loads(path.read_text())
        return ThrottleState(last_alert=data.get("last_alert", {}))
    except (json.JSONDecodeError, OSError):
        return ThrottleState(last_alert={})


def _save_state(state: ThrottleState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_alert": state.last_alert}, indent=2))


def is_throttled(
    key: str,
    cooldown: int = DEFAULT_COOLDOWN,
    state_path: Optional[Path] = None,
) -> bool:
    """Return True if an alert for *key* was sent within the cooldown window."""
    path = state_path or Path(".pipewatch") / "throttle.json"
    state = _load_state(path)
    last = state.last_alert.get(key)
    if last is None:
        return False
    return (time.time() - last) < cooldown


def record_alert(
    key: str,
    state_path: Optional[Path] = None,
) -> None:
    """Record that an alert for *key* was just sent."""
    path = state_path or Path(".pipewatch") / "throttle.json"
    state = _load_state(path)
    state.last_alert[key] = time.time()
    _save_state(state, path)


def maybe_send(
    key: str,
    send_fn,
    cooldown: int = DEFAULT_COOLDOWN,
    state_path: Optional[Path] = None,
) -> bool:
    """Call send_fn() unless throttled. Returns True if alert was sent."""
    if is_throttled(key, cooldown=cooldown, state_path=state_path):
        return False
    send_fn()
    record_alert(key, state_path=state_path)
    return True
