"""Persistent run log: records every pipeline execution with metadata for audit and replay."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RunLogEntry:
    command: str
    started_at: str
    finished_at: str
    exit_code: int
    success: bool
    timed_out: bool
    duration: float
    stderr: str = ""
    tags: List[str] = field(default_factory=list)
    run_id: Optional[str] = None


def to_dict(entry: RunLogEntry) -> dict:
    return {
        "command": entry.command,
        "started_at": entry.started_at,
        "finished_at": entry.finished_at,
        "exit_code": entry.exit_code,
        "success": entry.success,
        "timed_out": entry.timed_out,
        "duration": entry.duration,
        "stderr": entry.stderr,
        "tags": entry.tags,
        "run_id": entry.run_id,
    }


def from_dict(d: dict) -> RunLogEntry:
    return RunLogEntry(
        command=d.get("command", ""),
        started_at=d.get("started_at", ""),
        finished_at=d.get("finished_at", ""),
        exit_code=d.get("exit_code", 0),
        success=d.get("success", False),
        timed_out=d.get("timed_out", False),
        duration=d.get("duration", 0.0),
        stderr=d.get("stderr", ""),
        tags=d.get("tags", []),
        run_id=d.get("run_id"),
    )


def load_runlog(path: str) -> List[RunLogEntry]:
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, "r") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(from_dict(json.loads(line)))
                except (json.JSONDecodeError, KeyError):
                    continue
    return entries


def append_runlog(path: str, entry: RunLogEntry) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(to_dict(entry)) + "\n")


def filter_by_command(entries: List[RunLogEntry], command: str) -> List[RunLogEntry]:
    return [e for e in entries if e.command == command]


def filter_failures(entries: List[RunLogEntry]) -> List[RunLogEntry]:
    return [e for e in entries if not e.success]
