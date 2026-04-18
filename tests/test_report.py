"""Tests for pipewatch.report."""

from pipewatch.history import HistoryEntry
from pipewatch.report import summarize, filter_failures, _success_rate, _avg_duration


def _e(exit_code=0, timed_out=False, duration=1.0):
    return HistoryEntry(
        command="cmd",
        exit_code=exit_code,
        timed_out=timed_out,
        duration=duration,
        timestamp="2024-01-01T00:00:00+00:00",
    )


def test_success_rate_all_pass():
    entries = [_e(), _e(), _e()]
    assert _success_rate(entries) == 100.0


def test_success_rate_mixed():
    entries = [_e(), _e(exit_code=1), _e()]
    assert abs(_success_rate(entries) - 66.67) < 0.1


def test_success_rate_empty():
    assert _success_rate([]) == 0.0


def test_avg_duration():
    entries = [_e(duration=2.0), _e(duration=4.0)]
    assert _avg_duration(entries) == 3.0


def test_summarize_no_history():
    assert summarize([]) == "No history available."


def test_summarize_contains_rate():
    entries = [_e(), _e(exit_code=1)]
    out = summarize(entries)
    assert "50.0%" in out


def test_summarize_last_n():
    entries = [_e(exit_code=1)] * 5 + [_e()] * 5
    out = summarize(entries, last_n=5)
    assert "100.0%" in out


def test_filter_failures():
    entries = [_e(), _e(exit_code=1), _e(timed_out=True)]
    failures = filter_failures(entries)
    assert len(failures) == 2
