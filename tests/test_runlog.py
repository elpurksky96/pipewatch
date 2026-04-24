"""Tests for pipewatch.runlog."""

import json
import os
import pytest

from pipewatch.runlog import (
    RunLogEntry,
    to_dict,
    from_dict,
    load_runlog,
    append_runlog,
    filter_by_command,
    filter_failures,
)


def _entry(**kwargs) -> RunLogEntry:
    defaults = dict(
        command="etl.py",
        started_at="2024-01-01T00:00:00",
        finished_at="2024-01-01T00:01:00",
        exit_code=0,
        success=True,
        timed_out=False,
        duration=60.0,
        stderr="",
        tags=[],
        run_id="abc123",
    )
    defaults.update(kwargs)
    return RunLogEntry(**defaults)


def test_roundtrip_dict():
    e = _entry(tags=["prod", "nightly"])
    assert from_dict(to_dict(e)).tags == ["prod", "nightly"]
    assert from_dict(to_dict(e)).command == "etl.py"


def test_from_dict_defaults():
    e = from_dict({})
    assert e.command == ""
    assert e.success is False
    assert e.duration == 0.0
    assert e.tags == []
    assert e.run_id is None


def test_load_runlog_missing_file(tmp_path):
    result = load_runlog(str(tmp_path / "nonexistent.jsonl"))
    assert result == []


def test_append_and_load(tmp_path):
    path = str(tmp_path / "runlog.jsonl")
    e1 = _entry(command="job_a.py")
    e2 = _entry(command="job_b.py", success=False, exit_code=1)
    append_runlog(path, e1)
    append_runlog(path, e2)
    loaded = load_runlog(path)
    assert len(loaded) == 2
    assert loaded[0].command == "job_a.py"
    assert loaded[1].success is False


def test_load_skips_malformed_lines(tmp_path):
    path = str(tmp_path / "runlog.jsonl")
    with open(path, "w") as fh:
        fh.write(json.dumps(to_dict(_entry())) + "\n")
        fh.write("not valid json\n")
        fh.write(json.dumps(to_dict(_entry(command="other.py"))) + "\n")
    loaded = load_runlog(path)
    assert len(loaded) == 2


def test_filter_by_command():
    entries = [_entry(command="a.py"), _entry(command="b.py"), _entry(command="a.py")]
    result = filter_by_command(entries, "a.py")
    assert len(result) == 2
    assert all(e.command == "a.py" for e in result)


def test_filter_failures():
    entries = [
        _entry(success=True),
        _entry(success=False, exit_code=1),
        _entry(success=False, timed_out=True),
    ]
    result = filter_failures(entries)
    assert len(result) == 2
    assert all(not e.success for e in result)
