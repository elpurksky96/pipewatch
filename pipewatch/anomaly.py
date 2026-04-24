"""Anomaly detection for pipeline run durations using z-score analysis."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AnomalyResult:
    command: str
    duration: float
    mean: float
    stddev: float
    z_score: float
    is_anomaly: bool
    threshold: float

    @property
    def direction(self) -> str:
        return "slow" if self.duration > self.mean else "fast"


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _stddev(values: List[float], mean: float) -> float:
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def detect_anomaly(
    command: str,
    current_duration: float,
    historical_durations: List[float],
    threshold: float = 2.5,
    min_samples: int = 5,
) -> Optional[AnomalyResult]:
    """Return AnomalyResult if current_duration is anomalous, else None.

    Returns None when there are fewer than min_samples historical entries
    or when stddev is zero (all durations identical).
    """
    if len(historical_durations) < min_samples:
        return None

    mean = _mean(historical_durations)
    stddev = _stddev(historical_durations, mean)

    if stddev == 0.0:
        return None

    z_score = abs(current_duration - mean) / stddev
    is_anomaly = z_score >= threshold

    return AnomalyResult(
        command=command,
        duration=current_duration,
        mean=mean,
        stddev=stddev,
        z_score=z_score,
        is_anomaly=is_anomaly,
        threshold=threshold,
    )


def format_anomaly(result: AnomalyResult) -> str:
    """Return a human-readable summary of an anomaly result."""
    status = "ANOMALY" if result.is_anomaly else "normal"
    return (
        f"[{status}] {result.command}: duration={result.duration:.1f}s "
        f"(mean={result.mean:.1f}s, stddev={result.stddev:.1f}s, "
        f"z={result.z_score:.2f}, threshold={result.threshold}, "
        f"direction={result.direction})"
    )
