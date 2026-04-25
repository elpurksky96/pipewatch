"""Tests for pipewatch.retention."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest

from pipewatch.retention import (
    RetentionPolicy,
    apply_retention,
    parse_policy,
    policy_to_dict,
    prune_history_file,
)


def _ts(days_ago: float) -> str:
    dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_ago)
    return dt.isoformat()


def _entry(days_ago: float, success: bool = True) -> dict:
    return {"timestamp": _ts(days_ago), "success": success, "command": "echo hi"}


# ---------------------------------------------------------------------------
# parse_policy / policy_to_dict
# ---------------------------------------------------------------------------

def test_parse_policy_empty():
    p = parse_policy({})
    assert p.max_entries is None
    assert p.max_days is None


def test_parse_policy_full():
    p = parse_policy({"max_entries": 100, "max_days": 30.0})
    assert p.max_entries == 100
    assert p.max_days == 30.0


def test_policy_to_dict_roundtrip():
    p = RetentionPolicy(max_entries=50, max_days=7)
    assert policy_to_dict(p) == {"max_entries": 50, "max_days": 7}


def test_policy_to_dict_omits_none():
    p = RetentionPolicy(max_entries=10)
    d = policy_to_dict(p)
    assert "max_days" not in d


# ---------------------------------------------------------------------------
# apply_retention — max_entries
# ---------------------------------------------------------------------------

def test_max_entries_keeps_most_recent():
    entries = [_entry(i) for i in range(5, 0, -1)]  # oldest first
    result = apply_retention(entries, RetentionPolicy(max_entries=3))
    assert len(result) == 3
    assert result == entries[-3:]


def test_max_entries_no_op_when_under_limit():
    entries = [_entry(1), _entry(0.5)]
    result = apply_retention(entries, RetentionPolicy(max_entries=10))
    assert result == entries


# ---------------------------------------------------------------------------
# apply_retention — max_days
# ---------------------------------------------------------------------------

def test_max_days_drops_old_entries():
    entries = [_entry(10), _entry(5), _entry(1)]
    result = apply_retention(entries, RetentionPolicy(max_days=7))
    assert len(result) == 2  # 10-day-old entry removed


def test_max_days_keeps_all_when_recent():
    entries = [_entry(0.1), _entry(0.5)]
    result = apply_retention(entries, RetentionPolicy(max_days=7))
    assert len(result) == 2


def test_entry_without_timestamp_is_kept():
    entries = [{"success": True, "command": "x"}, _entry(100)]
    result = apply_retention(entries, RetentionPolicy(max_days=1))
    # entry without timestamp is preserved; 100-day-old is dropped
    assert any("timestamp" not in e for e in result)


# ---------------------------------------------------------------------------
# prune_history_file
# ---------------------------------------------------------------------------

def test_prune_history_file_removes_old(tmp_path: Path):
    hist = tmp_path / "history.jsonl"
    entries = [_entry(20), _entry(10), _entry(1)]
    hist.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

    removed = prune_history_file(hist, RetentionPolicy(max_days=15))
    assert removed == 1
    remaining = [json.loads(l) for l in hist.read_text().splitlines() if l.strip()]
    assert len(remaining) == 2


def test_prune_history_file_missing_is_noop(tmp_path: Path):
    removed = prune_history_file(tmp_path / "nope.jsonl", RetentionPolicy(max_entries=5))
    assert removed == 0


def test_prune_history_file_no_change_when_within_limits(tmp_path: Path):
    hist = tmp_path / "history.jsonl"
    entries = [_entry(1), _entry(0.5)]
    original = "\n".join(json.dumps(e) for e in entries) + "\n"
    hist.write_text(original)

    removed = prune_history_file(hist, RetentionPolicy(max_entries=10, max_days=30))
    assert removed == 0
    assert hist.read_text() == original
