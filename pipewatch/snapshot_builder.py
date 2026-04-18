"""Build a Snapshot from current history."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from pipewatch.history import HistoryEntry
from pipewatch.report import _success_rate, _avg_duration, _timeout_count
from pipewatch.snapshot import Snapshot


def build_snapshot(label: str, entries: List[HistoryEntry]) -> Snapshot:
    """Summarise *entries* into a Snapshot tagged with *label*."""
    return Snapshot(
        label=label,
        timestamp=datetime.now(timezone.utc).isoformat(),
        success_rate=round(_success_rate(entries), 4),
        avg_duration=round(_avg_duration(entries), 3),
        total_runs=len(entries),
        timeout_count=_timeout_count(entries),
    )


def format_diff(diff: dict) -> str:
    """Human-readable summary of snapshot diff."""
    if not diff:
        return "No changes since last snapshot."
    lines = []
    labels = {
        "success_rate": "Success rate",
        "avg_duration": "Avg duration (s)",
        "total_runs": "Total runs",
        "timeout_count": "Timeouts",
    }
    for field, (old, new) in diff.items():
        arrow = "▲" if new > old else "▼"
        lines.append(f"  {labels.get(field, field)}: {old} → {new} {arrow}")
    return "\n".join(lines)
