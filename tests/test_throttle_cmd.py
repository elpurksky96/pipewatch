"""Tests for pipewatch.throttle_cmd."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from pipewatch.throttle import record_alert
from pipewatch.throttle_cmd import cmd_throttle_reset, cmd_throttle_status


def _args(state, cooldown=3600, key=None):
    ns = argparse.Namespace()
    ns.state = str(state)
    ns.cooldown = cooldown
    ns.key = key
    return ns


def test_status_empty(tmp_path, capsys):
    path = tmp_path / "throttle.json"
    rc = cmd_throttle_status(_args(path))
    assert rc == 0
    assert "No throttle records" in capsys.readouterr().out


def test_status_shows_entries(tmp_path, capsys):
    path = tmp_path / "throttle.json"
    record_alert("my-job", state_path=path)
    rc = cmd_throttle_status(_args(path, cooldown=3600))
    assert rc == 0
    out = capsys.readouterr().out
    assert "my-job" in out
    assert "throttled" in out


def test_reset_all(tmp_path, capsys):
    path = tmp_path / "throttle.json"
    record_alert("job-a", state_path=path)
    record_alert("job-b", state_path=path)
    rc = cmd_throttle_reset(_args(path, key=None))
    assert rc == 0
    assert "cleared" in capsys.readouterr().out
    # After reset nothing is throttled
    from pipewatch.throttle import is_throttled
    assert not is_throttled("job-a", state_path=path)


def test_reset_specific_key(tmp_path, capsys):
    path = tmp_path / "throttle.json"
    record_alert("job-a", state_path=path)
    record_alert("job-b", state_path=path)
    rc = cmd_throttle_reset(_args(path, key="job-a"))
    assert rc == 0
    from pipewatch.throttle import is_throttled
    assert not is_throttled("job-a", state_path=path)
    assert is_throttled("job-b", state_path=path)


def test_reset_missing_key(tmp_path, capsys):
    path = tmp_path / "throttle.json"
    rc = cmd_throttle_reset(_args(path, key="nonexistent"))
    assert rc == 1
