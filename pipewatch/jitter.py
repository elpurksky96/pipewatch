"""Jitter detection: flag commands whose duration varies erratically over time."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class JitterResult:
    command: str
    sample_count: int
    mean: float
    stddev: float
    cv: float          # coefficient of variation = stddev / mean
    threshold: float
    is_jittery: bool
    message: str


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _stddev(values: Sequence[float], mean: float) -> float:
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def detect_jitter(
    command: str,
    durations: List[float],
    threshold: float = 0.5,
    min_samples: int = 5,
) -> Optional[JitterResult]:
    """Return a JitterResult if enough samples exist, else None.

    A run is considered jittery when the coefficient of variation
    (stddev / mean) exceeds *threshold* (default 0.5 = 50 %).
    """
    if len(durations) < min_samples:
        return None

    m = _mean(durations)
    if m == 0.0:
        return None

    sd = _stddev(durations, m)
    cv = sd / m
    is_jittery = cv > threshold

    if is_jittery:
        msg = (
            f"High duration jitter detected (CV={cv:.2f} > {threshold:.2f}): "
            f"mean={m:.1f}s stddev={sd:.1f}s over {len(durations)} runs"
        )
    else:
        msg = (
            f"Duration stable (CV={cv:.2f} <= {threshold:.2f}): "
            f"mean={m:.1f}s stddev={sd:.1f}s over {len(durations)} runs"
        )

    return JitterResult(
        command=command,
        sample_count=len(durations),
        mean=round(m, 3),
        stddev=round(sd, 3),
        cv=round(cv, 4),
        threshold=threshold,
        is_jittery=is_jittery,
        message=msg,
    )


def format_jitter(result: JitterResult) -> str:
    """Return a human-readable one-liner for CLI output."""
    status = "JITTERY" if result.is_jittery else "stable"
    return f"[{status}] {result.command}: {result.message}"
