"""Tests for pipewatch.history."""

import json
from pathlib import Path

import pytest

from pipewatch.history import (
    HistoryEntry,
    append_entry,
    load_history,
    make_entry,
)


def _entry(**kwargs) -> HistoryEntry:
    defaults = dict(command="echo hi", exit_code=0, timed_out=False, duration=1.5, timestamp="2024-01-01T00:00:00+00:00", stderr_tail="")
    defaults.update(kwargs)
    return HistoryEntry(**defaults)


def test_make_entry_fields():
    e = make_entry("cmd", 1, False, 2.5, "err")
    assert e.command == "cmd"
    assert e.exit_code == 1
    assert e.duration == 2.5
    assert e.stderr_tail == "err"
    assert e.timestamp  # non-empty


def test_roundtrip_dict():
    e = _entry(exit_code=1, timed_out=True)
    assert HistoryEntry.from_dict(e.to_dict()) == e


def test_load_history_missing_file(tmp_path):
    result = load_history(tmp_path / "nope.json")
    assert result == []


def test_append_and_load(tmp_path):
    p = tmp_path / "h.json"
    e = _entry(command="ls")
    append_entry(e, path=p)
    loaded = load_history(p)
    assert len(loaded) == 1
    assert loaded[0].command == "ls"


def test_append_multiple(tmp_path):
    p = tmp_path / "h.json"
    for i in range(3):
        append_entry(_entry(command=f"cmd{i}"), path=p)
    loaded = load_history(p)
    assert len(loaded) == 3
    assert loaded[2].command == "cmd2"


def test_max_entries_trimmed(tmp_path):
    p = tmp_path / "h.json"
    for i in range(10):
        append_entry(_entry(command=f"cmd{i}"), path=p, max_entries=5)
    loaded = load_history(p)
    assert len(loaded) == 5
    assert loaded[0].command == "cmd5"


def test_load_corrupt_file(tmp_path):
    p = tmp_path / "h.json"
    p.write_text("not json")
    assert load_history(p) == []
