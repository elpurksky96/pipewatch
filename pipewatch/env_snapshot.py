"""Capture and compare environment variable snapshots for pipeline runs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class EnvSnapshot:
    command: str
    timestamp: str
    variables: Dict[str, str] = field(default_factory=dict)


def to_dict(snap: EnvSnapshot) -> dict:
    return {
        "command": snap.command,
        "timestamp": snap.timestamp,
        "variables": snap.variables,
    }


def from_dict(d: dict) -> EnvSnapshot:
    return EnvSnapshot(
        command=d.get("command", ""),
        timestamp=d.get("timestamp", ""),
        variables=d.get("variables", {}),
    )


def capture_env(command: str, timestamp: str, prefix: Optional[str] = None) -> EnvSnapshot:
    """Capture current environment variables, optionally filtered by prefix."""
    variables = {
        k: v
        for k, v in os.environ.items()
        if prefix is None or k.startswith(prefix)
    }
    return EnvSnapshot(command=command, timestamp=timestamp, variables=variables)


def diff_snapshots(old: EnvSnapshot, new: EnvSnapshot) -> Dict[str, dict]:
    """Return a diff between two snapshots: added, removed, changed keys."""
    old_vars = old.variables
    new_vars = new.variables
    all_keys = set(old_vars) | set(new_vars)
    changes: Dict[str, dict] = {}
    for key in sorted(all_keys):
        if key not in old_vars:
            changes[key] = {"status": "added", "value": new_vars[key]}
        elif key not in new_vars:
            changes[key] = {"status": "removed", "old_value": old_vars[key]}
        elif old_vars[key] != new_vars[key]:
            changes[key] = {"status": "changed", "old": old_vars[key], "new": new_vars[key]}
    return changes


def load_env_snapshots(path: Path) -> List[EnvSnapshot]:
    if not path.exists():
        return []
    entries = json.loads(path.read_text())
    return [from_dict(e) for e in entries]


def save_env_snapshot(snap: EnvSnapshot, path: Path) -> None:
    existing = load_env_snapshots(path)
    existing.append(snap)
    path.write_text(json.dumps([to_dict(e) for e in existing], indent=2))


def latest_for_command(snapshots: List[EnvSnapshot], command: str) -> Optional[EnvSnapshot]:
    matches = [s for s in snapshots if s.command == command]
    return matches[-1] if matches else None
