"""Liveness probe support: record and check whether a command has run recently."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProbeEntry:
    command: str
    last_seen: str  # ISO-8601
    success: bool
    tags: List[str] = field(default_factory=list)


def to_dict(entry: ProbeEntry) -> dict:
    return {
        "command": entry.command,
        "last_seen": entry.last_seen,
        "success": entry.success,
        "tags": entry.tags,
    }


def from_dict(d: dict) -> ProbeEntry:
    return ProbeEntry(
        command=d["command"],
        last_seen=d["last_seen"],
        success=d.get("success", True),
        tags=d.get("tags", []),
    )


def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return json.load(fh)


def _save(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def record_probe(path: str, command: str, success: bool, tags: Optional[List[str]] = None) -> ProbeEntry:
    """Update the liveness record for *command*."""
    data = _load(path)
    entry = ProbeEntry(
        command=command,
        last_seen=_now_iso(),
        success=success,
        tags=tags or [],
    )
    data[command] = to_dict(entry)
    _save(path, data)
    return entry


def load_probe(path: str, command: str) -> Optional[ProbeEntry]:
    """Return the most recent probe entry for *command*, or None."""
    data = _load(path)
    raw = data.get(command)
    return from_dict(raw) if raw else None


def check_probe(path: str, command: str, max_age_seconds: float) -> bool:
    """Return True if *command* was seen within *max_age_seconds*."""
    entry = load_probe(path, command)
    if entry is None:
        return False
    last = datetime.fromisoformat(entry.last_seen)
    now = datetime.now(timezone.utc)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return (now - last).total_seconds() <= max_age_seconds


def list_probes(path: str) -> List[ProbeEntry]:
    """Return all recorded probe entries."""
    data = _load(path)
    return [from_dict(v) for v in data.values()]
