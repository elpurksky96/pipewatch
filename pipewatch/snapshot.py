"""Snapshot: capture and compare pipeline run metrics over time."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class Snapshot:
    label: str
    timestamp: str
    success_rate: float
    avg_duration: float
    total_runs: int
    timeout_count: int


def from_dict(d: dict) -> Snapshot:
    return Snapshot(
        label=d["label"],
        timestamp=d["timestamp"],
        success_rate=d["success_rate"],
        avg_duration=d["avg_duration"],
        total_runs=d["total_runs"],
        timeout_count=d["timeout_count"],
    )


def to_dict(s: Snapshot) -> dict:
    return asdict(s)


def load_snapshots(path: str) -> List[Snapshot]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        raw = json.load(f)
    return [from_dict(r) for r in raw]


def save_snapshot(path: str, snapshot: Snapshot) -> None:
    existing = load_snapshots(path)
    existing.append(snapshot)
    with open(path, "w") as f:
        json.dump([to_dict(s) for s in existing], f, indent=2)


def diff_snapshots(old: Snapshot, new: Snapshot) -> dict:
    """Return a dict of changed numeric fields with (old, new) tuples."""
    fields = ["success_rate", "avg_duration", "total_runs", "timeout_count"]
    return {
        field: (getattr(old, field), getattr(new, field))
        for field in fields
        if getattr(old, field) != getattr(new, field)
    }


def latest_snapshot(path: str) -> Optional[Snapshot]:
    snaps = load_snapshots(path)
    return snaps[-1] if snaps else None
