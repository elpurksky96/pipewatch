"""Deduplication of alerts based on content hashing.

Prevents sending repeated alerts for the same failure within a
configurable suppression window.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Optional

DEFAULT_STATE_PATH = Path(".pipewatch") / "dedup_state.json"


def _content_hash(command: str, stderr: str) -> str:
    """Return a short hash identifying this (command, stderr) pair."""
    raw = json.dumps({"command": command, "stderr": stderr}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _load(path: Path) -> Dict[str, float]:
    """Load dedup state mapping hash -> last_seen epoch."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(state: Dict[str, float], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def is_duplicate(
    command: str,
    stderr: str,
    window_seconds: float = 3600.0,
    state_path: Path = DEFAULT_STATE_PATH,
) -> bool:
    """Return True if an identical alert was already sent within *window_seconds*."""
    key = _content_hash(command, stderr)
    state = _load(state_path)
    last_seen: Optional[float] = state.get(key)
    if last_seen is None:
        return False
    return (time.time() - last_seen) < window_seconds


def record_sent(
    command: str,
    stderr: str,
    state_path: Path = DEFAULT_STATE_PATH,
) -> None:
    """Record that an alert for this (command, stderr) pair was just sent."""
    key = _content_hash(command, stderr)
    state = _load(state_path)
    state[key] = time.time()
    _save(state, state_path)


def prune_expired(
    window_seconds: float = 3600.0,
    state_path: Path = DEFAULT_STATE_PATH,
) -> int:
    """Remove entries older than *window_seconds*. Returns number removed."""
    state = _load(state_path)
    now = time.time()
    fresh = {k: v for k, v in state.items() if (now - v) < window_seconds}
    removed = len(state) - len(fresh)
    if removed:
        _save(fresh, state_path)
    return removed
