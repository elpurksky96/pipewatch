"""Tests for pipewatch.trend."""
import pytest
from pipewatch.trend import analyze_trend, format_trend, TrendSummary
from pipewatch.history import HistoryEntry


def _e(success: bool, duration: float = 1.0) -> HistoryEntry:
    return HistoryEntry(
        command="echo hi",
        timestamp="2024-01-01T00:00:00",
        success=success,
        timed_out=False,
        duration=duration,
        exit_code=0 if success else 1,
        stderr="",
    )


def test_all_success():
    entries = [_e(True)] * 8
    s = analyze_trend(entries)
    assert s.overall_success_rate == 1.0
    assert s.recent_success_rate == 1.0
    assert not s.is_degrading


def test_degrading_detected():
    # 5 successes then 5 failures
    entries = [_e(True)] * 5 + [_e(False)] * 5
    s = analyze_trend(entries, window=5)
    assert s.recent_success_rate == 0.0
    assert s.overall_success_rate == 0.5
    assert s.is_degrading


def test_not_degrading_when_improving():
    entries = [_e(False)] * 5 + [_e(True)] * 5
    s = analyze_trend(entries, window=5)
    assert not s.is_degrading


def test_slower_detected():
    entries = [_e(True, 1.0)] * 5 + [_e(True, 5.0)] * 5
    s = analyze_trend(entries, window=5)
    assert s.is_slower


def test_not_slower_within_threshold():
    entries = [_e(True, 1.0)] * 5 + [_e(True, 1.05)] * 5
    s = analyze_trend(entries, window=5)
    assert not s.is_slower


def test_empty_entries():
    s = analyze_trend([])
    assert s.total == 0
    assert s.overall_success_rate == 0.0
    assert not s.is_degrading


def test_fewer_than_window():
    entries = [_e(True), _e(False)]
    s = analyze_trend(entries, window=5)
    assert s.total == 2
    assert s.recent_success_rate == pytest.approx(0.5)


def test_format_trend_contains_key_info():
    entries = [_e(True)] * 5 + [_e(False)] * 5
    s = analyze_trend(entries, window=5)
    out = format_trend(s)
    assert "Total runs" in out
    assert "degrading" in out
