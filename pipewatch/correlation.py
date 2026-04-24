"""Correlate run history entries by shared labels or tags to find patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CorrelationGroup:
    key: str
    entries: List[object] = field(default_factory=list)
    total: int = 0
    failures: int = 0
    avg_duration: float = 0.0

    @property
    def failure_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.failures / self.total


def group_by_field(entries: List[object], field_name: str) -> Dict[str, CorrelationGroup]:
    """Group history entries by a named attribute (e.g. 'command', or a label key)."""
    groups: Dict[str, CorrelationGroup] = {}
    for entry in entries:
        value = getattr(entry, field_name, None)
        if value is None:
            continue
        key = str(value)
        if key not in groups:
            groups[key] = CorrelationGroup(key=key)
        groups[key].entries.append(entry)
    for group in groups.values():
        group.total = len(group.entries)
        group.failures = sum(
            1 for e in group.entries if not getattr(e, "success", True)
        )
        durations = [
            getattr(e, "duration", 0.0)
            for e in group.entries
            if getattr(e, "duration", None) is not None
        ]
        group.avg_duration = sum(durations) / len(durations) if durations else 0.0
    return groups


def find_correlated_failures(
    entries: List[object],
    field_name: str,
    min_failure_rate: float = 0.5,
    min_samples: int = 2,
) -> List[CorrelationGroup]:
    """Return groups whose failure rate exceeds the threshold."""
    groups = group_by_field(entries, field_name)
    return [
        g
        for g in groups.values()
        if g.total >= min_samples and g.failure_rate >= min_failure_rate
    ]


def format_correlation_report(
    groups: List[CorrelationGroup], field_name: str
) -> str:
    """Render a human-readable correlation report."""
    if not groups:
        return f"No correlated failures found by '{field_name}'."
    lines = [f"Correlated failures grouped by '{field_name}':"]
    for g in sorted(groups, key=lambda x: -x.failure_rate):
        pct = f"{g.failure_rate * 100:.1f}%"
        lines.append(
            f"  {g.key}: {g.failures}/{g.total} failures ({pct}), "
            f"avg duration {g.avg_duration:.2f}s"
        )
    return "\n".join(lines)
