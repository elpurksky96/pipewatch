"""Tests for pipewatch.quota_cmd."""

import argparse
import json
from pathlib import Path

import pytest

from pipewatch.quota import QuotaRule, record_run
from pipewatch.quota_cmd import (
    cmd_quota_check,
    cmd_quota_reset,
    cmd_quota_status,
)


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"rules": None, "state": None, "command": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def tmp_rules(tmp_path: Path) -> Path:
    return tmp_path / "quota_rules.json"


@pytest.fixture()
def tmp_state(tmp_path: Path) -> Path:
    return tmp_path / "quota_state.json"


def _write_rules(path: Path, rules: list) -> None:
    path.write_text(json.dumps(rules))


def test_status_no_rules(tmp_rules: Path, tmp_state: Path, capsys) -> None:
    args = _args(rules=str(tmp_rules), state=str(tmp_state))
    rc = cmd_quota_status(args)
    assert rc == 0
    assert "No quota rules" in capsys.readouterr().out


def test_status_shows_counts(tmp_rules: Path, tmp_state: Path, capsys) -> None:
    _write_rules(tmp_rules, [{"command": "etl:run", "max_runs": 5, "window_seconds": 60}])
    rule = QuotaRule("etl:run", 5, 60)
    record_run(rule, tmp_state)
    args = _args(rules=str(tmp_rules), state=str(tmp_state))
    rc = cmd_quota_status(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "etl:run" in out
    assert "1/5" in out
    assert "ok" in out


def test_check_no_rule(tmp_rules: Path, tmp_state: Path, capsys) -> None:
    _write_rules(tmp_rules, [])
    args = _args(rules=str(tmp_rules), state=str(tmp_state), command="missing:cmd")
    rc = cmd_quota_check(args)
    assert rc == 0
    assert "No quota rule" in capsys.readouterr().out


def test_check_within_quota(tmp_rules: Path, tmp_state: Path, capsys) -> None:
    _write_rules(tmp_rules, [{"command": "etl:run", "max_runs": 3, "window_seconds": 60}])
    args = _args(rules=str(tmp_rules), state=str(tmp_state), command="etl:run")
    rc = cmd_quota_check(args)
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_check_exceeded(tmp_rules: Path, tmp_state: Path, capsys) -> None:
    _write_rules(tmp_rules, [{"command": "etl:run", "max_runs": 1, "window_seconds": 60}])
    rule = QuotaRule("etl:run", 1, 60)
    record_run(rule, tmp_state)
    args = _args(rules=str(tmp_rules), state=str(tmp_state), command="etl:run")
    rc = cmd_quota_check(args)
    assert rc == 1
    assert "EXCEEDED" in capsys.readouterr().out


def test_reset_specific(tmp_rules: Path, tmp_state: Path, capsys) -> None:
    rule = QuotaRule("etl:run", 5, 60)
    record_run(rule, tmp_state)
    args = _args(rules=str(tmp_rules), state=str(tmp_state), command="etl:run")
    cmd_quota_reset(args)
    data = json.loads(tmp_state.read_text())
    assert "etl:run" not in data


def test_reset_all(tmp_rules: Path, tmp_state: Path, capsys) -> None:
    rule = QuotaRule("etl:run", 5, 60)
    record_run(rule, tmp_state)
    args = _args(rules=str(tmp_rules), state=str(tmp_state), command=None)
    cmd_quota_reset(args)
    data = json.loads(tmp_state.read_text())
    assert data == {}
