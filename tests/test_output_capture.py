"""Tests for pipewatch.output_capture."""
import json
import os

import pytest

from pipewatch.output_capture import (
    CapturedOutput, make_entry, to_dict, from_dict,
    save_output, load_outputs, filter_by_command,
)


def _entry(**kwargs) -> CapturedOutput:
    defaults = dict(command="echo hi", stdout="hi\n", stderr="", exit_code=0)
    defaults.update(kwargs)
    return make_entry(**defaults)


def test_make_entry_fields():
    e = _entry(command="ls", exit_code=1, timed_out=True, tags=["prod"])
    assert e.command == "ls"
    assert e.exit_code == 1
    assert e.timed_out is True
    assert "prod" in e.tags
    assert e.timestamp  # non-empty


def test_roundtrip_dict():
    e = _entry(tags=["nightly"])
    d = to_dict(e)
    e2 = from_dict(d)
    assert e2.command == e.command
    assert e2.stdout == e.stdout
    assert e2.tags == ["nightly"]
    assert e2.exit_code == e.exit_code


def test_from_dict_defaults():
    e = from_dict({})
    assert e.command == ""
    assert e.exit_code == 0
    assert e.timed_out is False
    assert e.tags == []


def test_load_outputs_missing_file(tmp_path):
    result = load_outputs(str(tmp_path / "nope.jsonl"))
    assert result == []


def test_save_and_load(tmp_path):
    path = str(tmp_path / "out.jsonl")
    e1 = _entry(command="cmd1", exit_code=0)
    e2 = _entry(command="cmd2", exit_code=1)
    save_output(e1, path)
    save_output(e2, path)
    loaded = load_outputs(path)
    assert len(loaded) == 2
    assert loaded[0].command == "cmd1"
    assert loaded[1].exit_code == 1


def test_save_appends(tmp_path):
    path = str(tmp_path / "out.jsonl")
    for i in range(3):
        save_output(_entry(command=f"cmd{i}"), path)
    assert len(load_outputs(path)) == 3


def test_filter_by_command(tmp_path):
    path = str(tmp_path / "out.jsonl")
    save_output(_entry(command="alpha"), path)
    save_output(_entry(command="beta"), path)
    save_output(_entry(command="alpha"), path)
    entries = load_outputs(path)
    filtered = filter_by_command(entries, "alpha")
    assert len(filtered) == 2
    assert all(e.command == "alpha" for e in filtered)
