"""Detect configuration or environment drift between pipeline runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DriftResult:
    command: str
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)

    @property
    def has_drift(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    @property
    def drift_count(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)


def detect_drift(
    command: str,
    baseline: Dict[str, str],
    current: Dict[str, str],
    ignore_keys: Optional[List[str]] = None,
) -> DriftResult:
    """Compare two key/value snapshots and return a DriftResult."""
    ignore = set(ignore_keys or [])
    baseline_filtered = {k: v for k, v in baseline.items() if k not in ignore}
    current_filtered = {k: v for k, v in current.items() if k not in ignore}

    baseline_keys = set(baseline_filtered)
    current_keys = set(current_filtered)

    added = {k: current_filtered[k] for k in current_keys - baseline_keys}
    removed = {k: baseline_filtered[k] for k in baseline_keys - current_keys}
    changed = {
        k: (baseline_filtered[k], current_filtered[k])
        for k in baseline_keys & current_keys
        if baseline_filtered[k] != current_filtered[k]
    }

    return DriftResult(command=command, added=added, removed=removed, changed=changed)


def format_drift(result: DriftResult) -> str:
    """Return a human-readable summary of detected drift."""
    if not result.has_drift:
        return f"[{result.command}] No drift detected."

    lines = [f"[{result.command}] Drift detected ({result.drift_count} change(s)):"]

    for k, v in sorted(result.added.items()):
        lines.append(f"  + {k}={v}")

    for k, v in sorted(result.removed.items()):
        lines.append(f"  - {k}={v}")

    for k, (old, new) in sorted(result.changed.items()):
        lines.append(f"  ~ {k}: {old!r} -> {new!r}")

    return "\n".join(lines)
