"""Tests for snapshot_builder.py."""
from pipewatch.snapshot_builder import build_snapshot, format_diff
from pipewatch.history import HistoryEntry


def _entry(success=True, duration=2.0, timed_out=False):
    return HistoryEntry(
        command="echo hi",
        started_at="2024-01-01T00:00:00+00:00",
        duration=duration,
        exit_code=0 if success else 1,
        timed_out=timed_out,
        success=success,
        stderr="",
    )


def test_build_snapshot_all_success():
    entries = [_entry() for _ in range(5)]
    snap = build_snapshot("ci", entries)
    assert snap.label == "ci"
    assert snap.success_rate == 1.0
    assert snap.total_runs == 5
    assert snap.timeout_count == 0


def test_build_snapshot_mixed():
    entries = [_entry(success=True)] * 3 + [_entry(success=False)] * 1
    snap = build_snapshot("ci", entries)
    assert snap.success_rate == 0.75
    assert snap.total_runs == 4


def test_build_snapshot_empty():
    snap = build_snapshot("ci", [])
    assert snap.total_runs == 0
    assert snap.success_rate == 0.0


def test_format_diff_no_changes():
    msg = format_diff({})
    assert "No changes" in msg


def test_format_diff_shows_fields():
    diff = {"success_rate": (0.8, 0.9), "timeout_count": (1, 0)}
    msg = format_diff(diff)
    assert "Success rate" in msg
    assert "▲" in msg
    assert "▼" in msg
