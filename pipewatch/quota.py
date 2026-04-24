"""Run quota enforcement: limit how many times a command can run in a time window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class QuotaRule:
    command: str
    max_runs: int
    window_seconds: int


@dataclass
class QuotaState:
    key: str
    timestamps: List[float] = field(default_factory=list)


def _load(path: Path) -> Dict[str, List[float]]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(path: Path, data: Dict[str, List[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _prune(timestamps: List[float], window_seconds: int, now: float) -> List[float]:
    cutoff = now - window_seconds
    return [t for t in timestamps if t >= cutoff]


def is_quota_exceeded(rule: QuotaRule, path: Path, now: Optional[float] = None) -> bool:
    """Return True if the command has reached its run quota within the window."""
    now = now if now is not None else time.time()
    data = _load(path)
    timestamps = _prune(data.get(rule.command, []), rule.window_seconds, now)
    return len(timestamps) >= rule.max_runs


def record_run(rule: QuotaRule, path: Path, now: Optional[float] = None) -> None:
    """Record a run timestamp for the given quota rule."""
    now = now if now is not None else time.time()
    data = _load(path)
    timestamps = _prune(data.get(rule.command, []), rule.window_seconds, now)
    timestamps.append(now)
    data[rule.command] = timestamps
    _save(path, data)


def current_count(rule: QuotaRule, path: Path, now: Optional[float] = None) -> int:
    """Return how many runs are recorded within the current window."""
    now = now if now is not None else time.time()
    data = _load(path)
    timestamps = _prune(data.get(rule.command, []), rule.window_seconds, now)
    return len(timestamps)


def parse_quota_rules(raw: List[Dict]) -> List[QuotaRule]:
    """Parse a list of dicts into QuotaRule objects."""
    rules = []
    for item in raw:
        rules.append(QuotaRule(
            command=item["command"],
            max_runs=int(item["max_runs"]),
            window_seconds=int(item.get("window_seconds", 3600)),
        ))
    return rules


def find_rule(rules: List[QuotaRule], command: str) -> Optional[QuotaRule]:
    for r in rules:
        if r.command == command:
            return r
    return None
