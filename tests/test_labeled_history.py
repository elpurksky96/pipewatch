"""Tests for pipewatch.labeled_history."""
import pytest
from unittest.mock import patch
from pipewatch.labeled_history import make_labeled_entry, load_labeled_history, summarize_by_label
from pipewatch.label import parse_labels, LabelSet
from pipewatch.history import HistoryEntry
import datetime


def _entry(success=True, duration=1.0, command="echo hi") -> HistoryEntry:
    return HistoryEntry(
        command=command,
        success=success,
        timed_out=False,
        duration=duration,
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0).isoformat(),
        exit_code=0 if success else 1,
        stderr="",
    )


def test_make_labeled_entry_has_labels():
    e = _entry()
    le = make_labeled_entry(e, ["env=prod"])
    assert le.labels.get("env") == "prod"
    assert le.command == "echo hi"


def test_make_labeled_entry_success_passthrough():
    le = make_labeled_entry(_entry(success=False), [])
    assert le.success is False


def test_load_labeled_history_missing_returns_empty():
    with patch("pipewatch.labeled_history.load_history", return_value=[]):
        result = load_labeled_history("/no/file", ["env=dev"])
    assert result == []


def test_load_labeled_history_attaches_labels():
    entries = [_entry(), _entry(success=False)]
    with patch("pipewatch.labeled_history.load_history", return_value=entries):
        result = load_labeled_history("/fake", ["env=staging"])
    assert all(r.labels.get("env") == "staging" for r in result)


def test_summarize_by_label_counts():
    from pipewatch.labeled_history import LabeledEntry
    e1 = LabeledEntry(entry=_entry(success=True, duration=2.0), labels=parse_labels(["env=prod"]))
    e2 = LabeledEntry(entry=_entry(success=False, duration=4.0), labels=parse_labels(["env=prod"]))
    e3 = LabeledEntry(entry=_entry(success=True, duration=1.0), labels=parse_labels(["env=dev"]))
    summary = summarize_by_label([e1, e2, e3], "env")
    assert summary["prod"]["total"] == 2
    assert summary["prod"]["passed"] == 1
    assert summary["dev"]["total"] == 1
    assert summary["dev"]["avg_duration"] == 1.0
