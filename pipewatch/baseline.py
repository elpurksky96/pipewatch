"""Baseline duration tracking: flag runs that exceed expected thresholds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import HistoryEntry


@dataclass
class BaselineStats:
    command: str
    sample_count: int
    avg_duration: float
    threshold: float  # avg * multiplier


@dataclass
class BaselineResult:
    stats: BaselineStats
    duration: float
    exceeded: bool
    ratio: float  # duration / threshold


def compute_baseline(
    entries: List[HistoryEntry],
    command: str,
    multiplier: float = 2.0,
) -> Optional[BaselineStats]:
    """Return baseline stats for *command* from successful history entries."""
    samples = [
        e.duration
        for e in entries
        if e.command == command and e.success and not e.timed_out
    ]
    if not samples:
        return None
    avg = sum(samples) / len(samples)
    return BaselineStats(
        command=command,
        sample_count=len(samples),
        avg_duration=avg,
        threshold=avg * multiplier,
    )


def check_baseline(
    stats: BaselineStats,
    duration: float,
) -> BaselineResult:
    """Compare *duration* against the pre-computed baseline threshold."""
    ratio = duration / stats.threshold if stats.threshold > 0 else 0.0
    return BaselineResult(
        stats=stats,
        duration=duration,
        exceeded=duration > stats.threshold,
        ratio=ratio,
    )


def format_baseline(result: BaselineResult) -> str:
    status = "EXCEEDED" if result.exceeded else "ok"
    return (
        f"Baseline [{result.stats.command}]: "
        f"{result.duration:.1f}s vs threshold {result.stats.threshold:.1f}s "
        f"(avg {result.stats.avg_duration:.1f}s x {result.stats.sample_count} samples) "
        f"— {status} ({result.ratio:.2f}x)"
    )
