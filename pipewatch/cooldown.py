"""Per-command alert cooldown with configurable window."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

DEFAULT_PATH = Path(".pipewatch") / "cooldown.json"


@dataclass
class CooldownState:
    last_alert: Dict[str, float] = field(default_factory=dict)


def _load(path: Path) -> CooldownState:
    if not path.exists():
        return CooldownState()
    try:
        data = json.loads(path.read_text())
        return CooldownState(last_alert=data.get("last_alert", {}))
    except (json.JSONDecodeError, OSError):
        return CooldownState()


def _save(state: CooldownState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_alert": state.last_alert}, indent=2))


def is_in_cooldown(key: str, window_seconds: int, path: Path = DEFAULT_PATH) -> bool:
    """Return True if key is still within its cooldown window."""
    state = _load(path)
    last = state.last_alert.get(key)
    if last is None:
        return False
    return (time.time() - last) < window_seconds


def record_alert(key: str, path: Path = DEFAULT_PATH, _now: Optional[float] = None) -> None:
    """Record that an alert was sent for key."""
    state = _load(path)
    state.last_alert[key] = _now if _now is not None else time.time()
    _save(state, path)


def reset(key: Optional[str] = None, path: Path = DEFAULT_PATH) -> None:
    """Reset cooldown for a specific key or all keys."""
    state = _load(path)
    if key is None:
        state.last_alert.clear()
    else:
        state.last_alert.pop(key, None)
    _save(state, path)


def describe(path: Path = DEFAULT_PATH) -> str:
    state = _load(path)
    if not state.last_alert:
        return "No cooldown entries."
    now = time.time()
    lines = []
    for k, ts in sorted(state.last_alert.items()):
        age = int(now - ts)
        lines.append(f"  {k}: last alert {age}s ago")
    return "\n".join(lines)
