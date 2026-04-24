"""Rate limiting for pipeline runs — prevents a command from running more
frequently than a configured minimum interval."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RateLimitState:
    last_run: Dict[str, float] = field(default_factory=dict)


def _load(path: str) -> RateLimitState:
    if not os.path.exists(path):
        return RateLimitState()
    with open(path) as fh:
        raw = json.load(fh)
    return RateLimitState(last_run=raw.get("last_run", {}))


def _save(path: str, state: RateLimitState) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"last_run": state.last_run}, fh, indent=2)


def is_rate_limited(path: str, key: str, min_interval_seconds: float) -> bool:
    """Return True if *key* has run more recently than *min_interval_seconds* ago."""
    state = _load(path)
    last = state.last_run.get(key)
    if last is None:
        return False
    return (time.time() - last) < min_interval_seconds


def record_run(path: str, key: str) -> None:
    """Record that *key* ran right now."""
    state = _load(path)
    state.last_run[key] = time.time()
    _save(path, state)


def seconds_until_allowed(path: str, key: str, min_interval_seconds: float) -> float:
    """Return how many seconds remain before *key* is allowed to run again.
    Returns 0.0 if it is already allowed.
    """
    state = _load(path)
    last = state.last_run.get(key)
    if last is None:
        return 0.0
    remaining = min_interval_seconds - (time.time() - last)
    return max(0.0, remaining)


def reset(path: str, key: Optional[str] = None) -> None:
    """Clear rate-limit state for *key*, or all keys if *key* is None."""
    state = _load(path)
    if key is None:
        state.last_run.clear()
    else:
        state.last_run.pop(key, None)
    _save(path, state)


def describe(path: str) -> Dict[str, float]:
    """Return a mapping of key -> seconds since last run (or -1 if never run)."""
    state = _load(path)
    now = time.time()
    return {
        k: round(now - v, 2)
        for k, v in state.last_run.items()
    }
