"""Heartbeat tracking: detect when a command stops running on schedule."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class HeartbeatEntry:
    command: str
    last_seen: float  # Unix timestamp
    interval_seconds: int  # expected max gap between runs


def to_dict(entry: HeartbeatEntry) -> dict:
    return {
        "command": entry.command,
        "last_seen": entry.last_seen,
        "interval_seconds": entry.interval_seconds,
    }


def from_dict(d: dict) -> HeartbeatEntry:
    return HeartbeatEntry(
        command=d["command"],
        last_seen=float(d["last_seen"]),
        interval_seconds=int(d.get("interval_seconds", 3600)),
    )


def _load_all(path: str) -> Dict[str, HeartbeatEntry]:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        raw = json.load(f)
    return {k: from_dict(v) for k, v in raw.items()}


def _save_all(path: str, entries: Dict[str, HeartbeatEntry]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump({k: to_dict(v) for k, v in entries.items()}, f, indent=2)


def record_heartbeat(path: str, command: str, interval_seconds: int = 3600) -> None:
    """Record that *command* ran right now."""
    entries = _load_all(path)
    entries[command] = HeartbeatEntry(
        command=command,
        last_seen=time.time(),
        interval_seconds=interval_seconds,
    )
    _save_all(path, entries)


@dataclass
class StalenessAlert:
    command: str
    last_seen: float
    interval_seconds: int
    seconds_overdue: float

    def overdue_minutes(self) -> float:
        return self.seconds_overdue / 60.0


def check_heartbeats(
    path: str, now: Optional[float] = None
) -> List[StalenessAlert]:
    """Return alerts for any command that has not been seen within its interval."""
    if now is None:
        now = time.time()
    entries = _load_all(path)
    alerts: List[StalenessAlert] = []
    for entry in entries.values():
        deadline = entry.last_seen + entry.interval_seconds
        if now > deadline:
            alerts.append(
                StalenessAlert(
                    command=entry.command,
                    last_seen=entry.last_seen,
                    interval_seconds=entry.interval_seconds,
                    seconds_overdue=now - deadline,
                )
            )
    return alerts


def format_heartbeat_report(alerts: List[StalenessAlert]) -> str:
    if not alerts:
        return "All heartbeats healthy."
    lines = ["Stale heartbeats detected:"]
    for a in alerts:
        lines.append(
            f"  {a.command}: overdue by {a.overdue_minutes():.1f} min "
            f"(interval {a.interval_seconds}s)"
        )
    return "\n".join(lines)
