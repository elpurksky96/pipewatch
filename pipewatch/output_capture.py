"""Capture and store stdout/stderr output from pipeline runs for later inspection."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

DEFAULT_CAPTURE_FILE = ".pipewatch_output.jsonl"


@dataclass
class CapturedOutput:
    command: str
    timestamp: str
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False
    tags: List[str] = field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_dict(entry: CapturedOutput) -> dict:
    return {
        "command": entry.command,
        "timestamp": entry.timestamp,
        "stdout": entry.stdout,
        "stderr": entry.stderr,
        "exit_code": entry.exit_code,
        "timed_out": entry.timed_out,
        "tags": entry.tags,
    }


def from_dict(d: dict) -> CapturedOutput:
    return CapturedOutput(
        command=d.get("command", ""),
        timestamp=d.get("timestamp", ""),
        stdout=d.get("stdout", ""),
        stderr=d.get("stderr", ""),
        exit_code=d.get("exit_code", 0),
        timed_out=d.get("timed_out", False),
        tags=d.get("tags", []),
    )


def make_entry(command: str, stdout: str, stderr: str, exit_code: int,
               timed_out: bool = False, tags: Optional[List[str]] = None) -> CapturedOutput:
    return CapturedOutput(
        command=command,
        timestamp=_now_iso(),
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        timed_out=timed_out,
        tags=tags or [],
    )


def save_output(entry: CapturedOutput, path: str = DEFAULT_CAPTURE_FILE) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(to_dict(entry)) + "\n")


def load_outputs(path: str = DEFAULT_CAPTURE_FILE) -> List[CapturedOutput]:
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(from_dict(json.loads(line)))
    return entries


def filter_by_command(entries: List[CapturedOutput], command: str) -> List[CapturedOutput]:
    return [e for e in entries if e.command == command]
