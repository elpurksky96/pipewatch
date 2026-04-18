"""Trend analysis for pipeline run history."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from pipewatch.history import HistoryEntry


@dataclass
class TrendSummary:
    total: int
    recent_success_rate: float  # last N runs
    overall_success_rate: float
    avg_duration_recent: float
    avg_duration_overall: float
    is_degrading: bool  # recent worse than overall
    is_slower: bool  # recent slower than overall


def _rate(entries: List[HistoryEntry]) -> float:
    if not entries:
        return 0.0
    return sum(1 for e in entries if e.success) / len(entries)


def _avg_dur(entries: List[HistoryEntry]) -> float:
    if not entries:
        return 0.0
    return sum(e.duration for e in entries) / len(entries)


def analyze_trend(entries: List[HistoryEntry], window: int = 5) -> TrendSummary:
    """Analyze recent vs overall performance."""
    recent = entries[-window:] if len(entries) >= window else entries[:]
    overall_rate = _rate(entries)
    recent_rate = _rate(recent)
    overall_dur = _avg_dur(entries)
    recent_dur = _avg_dur(recent)
    return TrendSummary(
        total=len(entries),
        recent_success_rate=recent_rate,
        overall_success_rate=overall_rate,
        avg_duration_recent=recent_dur,
        avg_duration_overall=overall_dur,
        is_degrading=recent_rate < overall_rate,
        is_slower=recent_dur > overall_dur * 1.1,
    )


def format_trend(summary: TrendSummary) -> str:
    lines = [
        f"Total runs      : {summary.total}",
        f"Overall success : {summary.overall_success_rate:.0%}",
        f"Recent success  : {summary.recent_success_rate:.0%}" +
            ("  ⚠ degrading" if summary.is_degrading else ""),
        f"Avg duration    : {summary.avg_duration_overall:.1f}s overall, "
            f"{summary.avg_duration_recent:.1f}s recent" +
            ("  ⚠ slower" if summary.is_slower else ""),
    ]
    return "\n".join(lines)
