"""Tests for pipewatch.circuit_cmd."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from pipewatch.circuit_breaker import record_outcome
from pipewatch.circuit_cmd import cmd_circuit_reset, cmd_circuit_status, dispatch


def _args(**kwargs):
    base = {"state_path": None, "func": None, "command": None}
    base.update(kwargs)
    return SimpleNamespace(**base)


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "cb.json"


def test_status_empty(state_path, capsys):
    args = _args(state_path=state_path)
    rc = cmd_circuit_status(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "No circuit" in out


def test_status_shows_entry(state_path, capsys):
    for _ in range(3):
        record_outcome("etl_job", success=False, threshold=3, path=state_path)
    args = _args(state_path=state_path)
    cmd_circuit_status(args)
    out = capsys.readouterr().out
    assert "etl_job" in out
    assert "OPEN" in out


def test_reset_specific_command(state_path, capsys):
    for _ in range(3):
        record_outcome("etl_job", success=False, threshold=3, path=state_path)
    args = _args(state_path=state_path, command="etl_job")
    rc = cmd_circuit_reset(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "etl_job" in out


def test_reset_all(state_path, capsys):
    for cmd in ("a", "b"):
        for _ in range(3):
            record_outcome(cmd, success=False, threshold=3, path=state_path)
    args = _args(state_path=state_path, command=None)
    rc = cmd_circuit_reset(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "2 circuit" in out


def test_dispatch_no_func_returns_1(capsys):
    args = _args()
    rc = dispatch(args)
    assert rc == 1


def test_dispatch_calls_func():
    called = {}

    def fake_func(a):
        called["yes"] = True
        return 0

    args = _args(func=fake_func)
    rc = dispatch(args)
    assert rc == 0
    assert called.get("yes")
