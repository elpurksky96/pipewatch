"""Tests for pipewatch.baseline."""

from __future__ import annotations

import pytest

from pipewatch.baseline import (
    BaselineStats,
    check_baseline,
    compute_baseline,
    format_baseline,
)
from pipewatch.history import HistoryEntry


def _entry(command: str, duration: float, success: bool = True, timed_out: bool = False) -> HistoryEntry:
    return HistoryEntry(
        command=command,
        timestamp="2024-01-01T00:00:00",
        duration=duration,
        success=success,
        timed_out=timed_out,
        exit_code=0 if success else 1,
        stderr="",
    )


def test_compute_baseline_basic():
    entries = [_entry("etl", 10.0), _entry("etl", 20.0), _entry("etl", 30.0)]
    stats = compute_baseline(entries, "etl")
    assert stats is not None
    assert stats.avg_duration == pytest.approx(20.0)
    assert stats.threshold == pytest.approx(40.0)
    assert stats.sample_count == 3


def test_compute_baseline_excludes_failures():
    entries = [_entry("etl", 10.0), _entry("etl", 999.0, success=False)]
    stats = compute_baseline(entries, "etl")
    assert stats.sample_count == 1
    assert stats.avg_duration == pytest.approx(10.0)


def test_compute_baseline_excludes_timeouts():
    entries = [_entry("etl", 10.0), _entry("etl", 500.0, timed_out=True)]
    stats = compute_baseline(entries, "etl")
    assert stats.sample_count == 1


def test_compute_baseline_no_matching_entries():
    entries = [_entry("other", 10.0)]
    assert compute_baseline(entries, "etl") is None


def test_check_baseline_not_exceeded():
    stats = BaselineStats(command="etl", sample_count=3, avg_duration=20.0, threshold=40.0)
    result = check_baseline(stats, 35.0)
    assert not result.exceeded
    assert result.ratio == pytest.approx(35.0 / 40.0)


def test_check_baseline_exceeded():
    stats = BaselineStats(command="etl", sample_count=3, avg_duration=20.0, threshold=40.0)
    result = check_baseline(stats, 50.0)
    assert result.exceeded
    assert result.ratio == pytest.approx(50.0 / 40.0)


def test_format_baseline_exceeded():
    stats = BaselineStats(command="etl", sample_count=5, avg_duration=20.0, threshold=40.0)
    result = check_baseline(stats, 80.0)
    text = format_baseline(result)
    assert "EXCEEDED" in text
    assert "etl" in text


def test_format_baseline_ok():
    stats = BaselineStats(command="etl", sample_count=5, avg_duration=20.0, threshold=40.0)
    result = check_baseline(stats, 10.0)
    text = format_baseline(result)
    assert "ok" in text
