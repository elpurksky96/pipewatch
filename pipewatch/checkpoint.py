"""Checkpoint support: persist named progress markers for long-running pipelines."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Checkpoint:
    name: str
    command: str
    reached_at: str
    metadata: Dict[str, str] = field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_dict(cp: Checkpoint) -> dict:
    return {
        "name": cp.name,
        "command": cp.command,
        "reached_at": cp.reached_at,
        "metadata": cp.metadata,
    }


def from_dict(d: dict) -> Checkpoint:
    return Checkpoint(
        name=d["name"],
        command=d["command"],
        reached_at=d["reached_at"],
        metadata=d.get("metadata", {}),
    )


def load_checkpoints(path: str) -> List[Checkpoint]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        raw = json.load(f)
    return [from_dict(r) for r in raw]


def save_checkpoint(path: str, name: str, command: str, metadata: Optional[Dict[str, str]] = None) -> Checkpoint:
    checkpoints = load_checkpoints(path)
    cp = Checkpoint(
        name=name,
        command=command,
        reached_at=_now_iso(),
        metadata=metadata or {},
    )
    # Replace existing checkpoint with same name+command or append
    updated = [c for c in checkpoints if not (c.name == name and c.command == command)]
    updated.append(cp)
    with open(path, "w") as f:
        json.dump([to_dict(c) for c in updated], f, indent=2)
    return cp


def get_checkpoint(path: str, name: str, command: str) -> Optional[Checkpoint]:
    for cp in load_checkpoints(path):
        if cp.name == name and cp.command == command:
            return cp
    return None


def clear_checkpoints(path: str, command: Optional[str] = None) -> int:
    checkpoints = load_checkpoints(path)
    if command is None:
        removed = len(checkpoints)
        with open(path, "w") as f:
            json.dump([], f)
        return removed
    kept = [c for c in checkpoints if c.command != command]
    removed = len(checkpoints) - len(kept)
    with open(path, "w") as f:
        json.dump([to_dict(c) for c in kept], f, indent=2)
    return removed
