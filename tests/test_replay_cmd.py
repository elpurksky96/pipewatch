"""Tests for pipewatch.replay_cmd."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

import pytest

from pipewatch.replay_cmd import cmd_replay_dry_run, cmd_replay_list, dispatch


def _write_history(path: str, entries: list[Dict[str, Any]]) -> None:
    with open(path, "w") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")


def _entry(command: str, success: bool, duration: float = 2.5) -> Dict[str, Any]:
    return {
        "command": command,
        "success": success,
        "duration": duration,
        "timestamp": "2024-06-01T12:00:00",
        "exit_code": 0 if success else 1,
        "stderr": "",
        "timed_out": False,
        "tags": [],
    }


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "command": "my_cmd",
        "history": "/dev/null",
        "limit": None,
        "only_failures": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_replay_list_no_history(tmp_path, capsys):
    p = tmp_path / "hist.json"
    rc = cmd_replay_list(_args(history=str(p)))
    out = capsys.readouterr().out
    assert rc == 0
    assert "No history" in out


def test_cmd_replay_list_shows_entries(tmp_path, capsys):
    p = tmp_path / "hist.json"
    _write_history(str(p), [
        _entry("my_cmd", True),
        _entry("my_cmd", False),
    ])
    rc = cmd_replay_list(_args(history=str(p)))
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK" in out
    assert "FAIL" in out


def test_cmd_replay_dry_run_prints_summary(tmp_path, capsys):
    p = tmp_path / "hist.json"
    _write_history(str(p), [_entry("my_cmd", True), _entry("my_cmd", False)])
    rc = cmd_replay_dry_run(_args(history=str(p)))
    out = capsys.readouterr().out
    assert rc == 0
    assert "my_cmd" in out
    assert "Would replay" in out


def test_cmd_replay_dry_run_only_failures(tmp_path, capsys):
    p = tmp_path / "hist.json"
    _write_history(str(p), [
        _entry("my_cmd", True),
        _entry("my_cmd", False),
    ])
    rc = cmd_replay_dry_run(_args(history=str(p), only_failures=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert "Skipped" in out


def test_dispatch_no_subcommand_returns_1(capsys):
    args = argparse.Namespace(replay_cmd=None)
    rc = dispatch(args)
    assert rc == 1
