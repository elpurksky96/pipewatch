"""Tests for pipewatch.baseline_cmd."""

from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from pipewatch.baseline_cmd import add_baseline_subparser, cmd_baseline
from pipewatch.history import HistoryEntry


def _entry(command: str, duration: float, success: bool = True) -> HistoryEntry:
    return HistoryEntry(
        command=command,
        timestamp="2024-01-01T00:00:00",
        duration=duration,
        success=success,
        timed_out=False,
        exit_code=0 if success else 1,
        stderr="",
    )


def _args(command: str = "etl", multiplier: float = 2.0) -> argparse.Namespace:
    return argparse.Namespace(
        command=command,
        history_file=".pipewatch_history.jsonl",
        multiplier=multiplier,
    )


def test_cmd_baseline_no_history(capsys):
    with patch("pipewatch.baseline_cmd.load_history", return_value=[]):
        rc = cmd_baseline(_args())
    assert rc == 1


def test_cmd_baseline_no_matching_command(capsys):
    entries = [_entry("other", 10.0)]
    with patch("pipewatch.baseline_cmd.load_history", return_value=entries):
        rc = cmd_baseline(_args(command="etl"))
    assert rc == 1


def test_cmd_baseline_within_threshold(capsys):
    entries = [_entry("etl", 10.0), _entry("etl", 10.0), _entry("etl", 10.0)]
    with patch("pipewatch.baseline_cmd.load_history", return_value=entries):
        rc = cmd_baseline(_args(command="etl", multiplier=2.0))
    out = capsys.readouterr().out
    assert rc == 0
    assert "ok" in out


def test_cmd_baseline_exceeded(capsys):
    base = [_entry("etl", 10.0)] * 5
    spike = [_entry("etl", 100.0)]
    with patch("pipewatch.baseline_cmd.load_history", return_value=base + spike):
        rc = cmd_baseline(_args(command="etl", multiplier=2.0))
    out = capsys.readouterr().out
    assert rc == 1
    assert "EXCEEDED" in out


def test_add_baseline_subparser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_baseline_subparser(sub)
    ns = parser.parse_args(["baseline", "my-cmd", "--multiplier", "3.0"])
    assert ns.command == "my-cmd"
    assert ns.multiplier == pytest.approx(3.0)
