"""Tests for pipewatch.env_snapshot."""

import json
from pathlib import Path

import pytest

from pipewatch.env_snapshot import (
    EnvSnapshot,
    capture_env,
    diff_snapshots,
    from_dict,
    latest_for_command,
    load_env_snapshots,
    save_env_snapshot,
    to_dict,
)


def _snap(command="cmd", timestamp="2024-01-01T00:00:00", variables=None):
    return EnvSnapshot(
        command=command,
        timestamp=timestamp,
        variables=variables or {"FOO": "bar", "BAZ": "qux"},
    )


def test_roundtrip_dict():
    s = _snap()
    assert from_dict(to_dict(s)).variables == s.variables
    assert from_dict(to_dict(s)).command == s.command


def test_from_dict_defaults():
    s = from_dict({})
    assert s.command == ""
    assert s.variables == {}


def test_capture_env_returns_snapshot(monkeypatch):
    monkeypatch.setenv("PIPEWATCH_TEST_VAR", "hello")
    snap = capture_env("my_cmd", "2024-01-01T00:00:00")
    assert snap.command == "my_cmd"
    assert "PIPEWATCH_TEST_VAR" in snap.variables
    assert snap.variables["PIPEWATCH_TEST_VAR"] == "hello"


def test_capture_env_with_prefix(monkeypatch):
    monkeypatch.setenv("PW_ALPHA", "1")
    monkeypatch.setenv("PW_BETA", "2")
    monkeypatch.setenv("OTHER_VAR", "3")
    snap = capture_env("cmd", "ts", prefix="PW_")
    assert "PW_ALPHA" in snap.variables
    assert "PW_BETA" in snap.variables
    assert "OTHER_VAR" not in snap.variables


def test_diff_added():
    old = _snap(variables={"A": "1"})
    new = _snap(variables={"A": "1", "B": "2"})
    diff = diff_snapshots(old, new)
    assert "B" in diff
    assert diff["B"]["status"] == "added"


def test_diff_removed():
    old = _snap(variables={"A": "1", "B": "2"})
    new = _snap(variables={"A": "1"})
    diff = diff_snapshots(old, new)
    assert diff["B"]["status"] == "removed"


def test_diff_changed():
    old = _snap(variables={"A": "1"})
    new = _snap(variables={"A": "99"})
    diff = diff_snapshots(old, new)
    assert diff["A"]["status"] == "changed"
    assert diff["A"]["old"] == "1"
    assert diff["A"]["new"] == "99"


def test_diff_no_changes():
    s = _snap(variables={"X": "1"})
    assert diff_snapshots(s, s) == {}


def test_load_missing_file_returns_empty(tmp_path):
    result = load_env_snapshots(tmp_path / "missing.json")
    assert result == []


def test_save_and_load(tmp_path):
    p = tmp_path / "env.json"
    s = _snap()
    save_env_snapshot(s, p)
    loaded = load_env_snapshots(p)
    assert len(loaded) == 1
    assert loaded[0].command == s.command


def test_save_appends(tmp_path):
    p = tmp_path / "env.json"
    save_env_snapshot(_snap(command="a"), p)
    save_env_snapshot(_snap(command="b"), p)
    loaded = load_env_snapshots(p)
    assert len(loaded) == 2


def test_latest_for_command():
    snaps = [
        _snap(command="cmd", timestamp="2024-01-01T00:00:00"),
        _snap(command="cmd", timestamp="2024-01-02T00:00:00"),
        _snap(command="other", timestamp="2024-01-03T00:00:00"),
    ]
    latest = latest_for_command(snaps, "cmd")
    assert latest is not None
    assert latest.timestamp == "2024-01-02T00:00:00"


def test_latest_for_command_missing():
    assert latest_for_command([], "nope") is None
