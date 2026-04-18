"""Generate summary reports from run history."""

from __future__ import annotations

from typing import List

from pipewatch.history import HistoryEntry
from pipewatch.format import format_duration


def _success_rate(entries: List[HistoryEntry]) -> float:
    if not entries:
        return 0.0
    successes = sum(1 for e in entries if e.exit_code == 0 and not e.timed_out)
    return successes / len(entries) * 100


def _avg_duration(entries: List[HistoryEntry]) -> float:
    if not entries:
        return 0.0
    return sum(e.duration for e in entries) / len(entries)


def _timeout_count(entries: List[HistoryEntry]) -> int:
    return sum(1 for e in entries if e.timed_out)


def summarize(entries: List[HistoryEntry], last_n: int = 20) -> str:
    subset = entries[-last_n:] if len(entries) > last_n else entries
    if not subset:
        return "No history available."

    lines = [
        f"Last {len(subset)} run(s):",
        f"  Success rate : {_success_rate(subset):.1f}%",
        f"  Avg duration : {format_duration(_avg_duration(subset))}",
        f"  Timeouts     : {_timeout_count(subset)}",
    ]

    last = subset[-1]
    status = "OK" if last.exit_code == 0 and not last.timed_out else ("TIMEOUT" if last.timed_out else f"FAIL({last.exit_code})")
    lines.append(f"  Last run     : {status} at {last.timestamp}")
    return "\n".join(lines)


def filter_failures(entries: List[HistoryEntry]) -> List[HistoryEntry]:
    return [e for e in entries if e.exit_code != 0 or e.timed_out]
