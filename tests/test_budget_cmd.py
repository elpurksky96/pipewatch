"""Tests for pipewatch.budget_cmd."""

import argparse
import json
from pathlib import Path

import pytest
from pipewatch.budget_cmd import cmd_budget_check, cmd_budget_list
from pipewatch.history import HistoryEntry, append_entry


def _args(tmp_path: Path, command: str = "etl.py") -> argparse.Namespace:
    return argparse.Namespace(
        command=command,
        budget_file=str(tmp_path / "budgets.json"),
        history_file=str(tmp_path / "history.json"),
    )


def _write_budgets(path: Path, rules: list) -> None:
    path.write_text(json.dumps(rules))


def _write_history_entry(history_file: str, command: str, duration: float, success: bool = True) -> None:
    entry = HistoryEntry(
        command=command,
        success=success,
        duration=duration,
        timed_out=False,
        timestamp="2024-01-01T00:00:00",
        stderr="",
        tags=[],
    )
    append_entry(history_file, entry)


def test_cmd_budget_check_no_rule(tmp_path):
    args = _args(tmp_path)
    _write_budgets(tmp_path / "budgets.json", [])
    _write_history_entry(args.history_file, "etl.py", 30.0)
    rc = cmd_budget_check(args)
    assert rc == 1


def test_cmd_budget_check_within_budget(tmp_path, capsys):
    args = _args(tmp_path)
    _write_budgets(tmp_path / "budgets.json", [{"command": "etl.py", "max_seconds": 120}])
    _write_history_entry(args.history_file, "etl.py", 45.0)
    rc = cmd_budget_check(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "BUDGET OK" in out


def test_cmd_budget_check_exceeded(tmp_path, capsys):
    args = _args(tmp_path)
    _write_budgets(tmp_path / "budgets.json", [{"command": "etl.py", "max_seconds": 30}])
    _write_history_entry(args.history_file, "etl.py", 90.0)
    rc = cmd_budget_check(args)
    out = capsys.readouterr().out
    assert rc == 1
    assert "BUDGET EXCEEDED" in out


def test_cmd_budget_check_no_history(tmp_path):
    args = _args(tmp_path)
    _write_budgets(tmp_path / "budgets.json", [{"command": "etl.py", "max_seconds": 60}])
    rc = cmd_budget_check(args)
    assert rc == 1


def test_cmd_budget_list_empty(tmp_path, capsys):
    args = _args(tmp_path)
    rc = cmd_budget_list(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "No budget rules" in out


def test_cmd_budget_list_shows_rules(tmp_path, capsys):
    args = _args(tmp_path)
    _write_budgets(
        tmp_path / "budgets.json",
        [{"command": "etl.py", "max_seconds": 60, "warn_seconds": 45}],
    )
    rc = cmd_budget_list(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "etl.py" in out
    assert "60" in out
    assert "45" in out
