"""Lightweight numeric metric tracking for pipeline runs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MetricPoint:
    command: str
    name: str
    value: float
    timestamp: str
    tags: Dict[str, str] = field(default_factory=dict)


def to_dict(mp: MetricPoint) -> dict:
    return {
        "command": mp.command,
        "name": mp.name,
        "value": mp.value,
        "timestamp": mp.timestamp,
        "tags": mp.tags,
    }


def from_dict(d: dict) -> MetricPoint:
    return MetricPoint(
        command=d["command"],
        name=d["name"],
        value=float(d["value"]),
        timestamp=d["timestamp"],
        tags=d.get("tags", {}),
    )


def load_metrics(path: str) -> List[MetricPoint]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [from_dict(line) for line in (json.loads(l) for l in f) if line]


def save_metric(path: str, mp: MetricPoint) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(to_dict(mp)) + "\n")


def filter_metrics(
    points: List[MetricPoint],
    command: Optional[str] = None,
    name: Optional[str] = None,
) -> List[MetricPoint]:
    result = points
    if command is not None:
        result = [p for p in result if p.command == command]
    if name is not None:
        result = [p for p in result if p.name == name]
    return result


def aggregate(points: List[MetricPoint]) -> Dict[str, float]:
    if not points:
        return {}
    values = [p.value for p in points]
    return {
        "count": float(len(values)),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "last": values[-1],
    }
