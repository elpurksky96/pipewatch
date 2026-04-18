"""Persist and retrieve run history for pipewatch jobs."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_FILE = Path.home() / ".pipewatch" / "history.json"
MAX_HISTORY_ENTRIES = 500


@dataclass
class HistoryEntry:
    command: str
    exit_code: int
    timed_out: bool
    duration: float
    timestamp: str  # ISO-8601
    stderr_tail: str = ""

    @staticmethod
    def from_dict(d: dict) -> "HistoryEntry":
        return HistoryEntry(
            command=d["command"],
            exit_code=d["exit_code"],
            timed_out=d["timed_out"],
            duration=d["duration"],
            timestamp=d["timestamp"],
            stderr_tail=d.get("stderr_tail", ""),
        )

    def to_dict(self) -> dict:
        return asdict(self)


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        with path.open() as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def load_history(path: Path = DEFAULT_HISTORY_FILE) -> List[HistoryEntry]:
    return [HistoryEntry.from_dict(d) for d in _load_raw(path)]


def append_entry(
    entry: HistoryEntry,
    path: Path = DEFAULT_HISTORY_FILE,
    max_entries: int = MAX_HISTORY_ENTRIES,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = _load_raw(path)
    entries.append(entry.to_dict())
    if len(entries) > max_entries:
        entries = entries[-max_entries:]
    with path.open("w") as f:
        json.dump(entries, f, indent=2)


def make_entry(command: str, exit_code: int, timed_out: bool, duration: float, stderr_tail: str = "") -> HistoryEntry:
    ts = datetime.now(timezone.utc).isoformat()
    return HistoryEntry(
        command=command,
        exit_code=exit_code,
        timed_out=timed_out,
        duration=duration,
        timestamp=ts,
        stderr_tail=stderr_tail,
    )
