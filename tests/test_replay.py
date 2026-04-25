"""Tests for pipewatch.replay."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import pytest

from pipewatch.replay import (
    ReplayResult,
    format_replay_summary,
    load_entries_for_command,
    replay,
)


def _write_history(path: str, entries: list[Dict[str, Any]]) -> None:
    with open(path, "w") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")


def _entry(command: str, success: bool, duration: float = 1.0) -> Dict[str, Any]:
    return {
        "command": command,
        "success": success,
        "duration": duration,
        "timestamp": "2024-01-01T00:00:00",
        "exit_code": 0 if success else 1,
        "stderr": "",
        "timed_out": False,
        "tags": [],
    }


def test_load_entries_for_command_filters(tmp_path):
    p = tmp_path / "hist.json"
    _write_history(str(p), [
        _entry("cmd_a", True),
        _entry("cmd_b", False),
        _entry("cmd_a", False),
    ])
    entries = load_entries_for_command("cmd_a", str(p))
    assert len(entries) == 2
    assert all(e.command == "cmd_a" for e in entries)


def test_load_entries_respects_limit(tmp_path):
    p = tmp_path / "hist.json"
    _write_history(str(p), [_entry("cmd", True) for _ in range(10)])
    entries = load_entries_for_command("cmd", str(p), limit=3)
    assert len(entries) == 3


def test_load_entries_missing_file_returns_empty(tmp_path):
    p = tmp_path / "missing.json"
    entries = load_entries_for_command("cmd", str(p))
    assert entries == []


def test_replay_counts_all(tmp_path):
    p = tmp_path / "hist.json"
    _write_history(str(p), [
        _entry("cmd", True),
        _entry("cmd", False),
        _entry("cmd", True),
    ])
    result = replay("cmd", str(p))
    assert result.replayed == 3
    assert result.skipped == 0


def test_replay_only_failures(tmp_path):
    p = tmp_path / "hist.json"
    _write_history(str(p), [
        _entry("cmd", True),
        _entry("cmd", False),
        _entry("cmd", False),
    ])
    result = replay("cmd", str(p), only_failures=True)
    assert result.replayed == 2
    assert result.skipped == 1


def test_format_replay_summary_contains_command(tmp_path):
    p = tmp_path / "hist.json"
    _write_history(str(p), [_entry("my_pipeline", True)])
    result = replay("my_pipeline", str(p))
    summary = format_replay_summary(result)
    assert "my_pipeline" in summary
    assert "Would replay" in summary


def test_replay_result_no_errors_by_default(tmp_path):
    p = tmp_path / "hist.json"
    _write_history(str(p), [_entry("cmd", True)])
    result = replay("cmd", str(p))
    assert result.errors == []
