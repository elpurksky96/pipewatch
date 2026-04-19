"""Tests for pipewatch.escalation_cmd."""
import argparse
import pytest
from pathlib import Path
from pipewatch.escalation import record_failure, mark_escalated
from pipewatch.escalation_cmd import cmd_escalation_status, cmd_escalation_reset


def _args(tmp_path, **kwargs):
    ns = argparse.Namespace(state_path=str(tmp_path / "esc.json"), **kwargs)
    return ns


def test_status_empty(tmp_path, capsys):
    rc = cmd_escalation_status(_args(tmp_path))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No escalation" in out


def test_status_shows_entries(tmp_path, capsys):
    path = tmp_path / "esc.json"
    record_failure("etl_job", path)
    record_failure("etl_job", path)
    mark_escalated("etl_job", path)
    rc = cmd_escalation_status(_args(tmp_path))
    assert rc == 0
    out = capsys.readouterr().out
    assert "etl_job" in out
    assert "2" in out
    assert "ESCALATED" in out


def test_reset_all(tmp_path, capsys):
    path = tmp_path / "esc.json"
    record_failure("job1", path)
    record_failure("job2", path)
    rc = cmd_escalation_reset(_args(tmp_path, key=None))
    assert rc == 0
    from pipewatch.escalation import _load_all
    assert _load_all(path) == {}


def test_reset_specific_key(tmp_path, capsys):
    path = tmp_path / "esc.json"
    record_failure("job1", path)
    record_failure("job2", path)
    rc = cmd_escalation_reset(_args(tmp_path, key="job1"))
    assert rc == 0
    from pipewatch.escalation import _load_all
    data = _load_all(path)
    assert "job1" not in data
    assert "job2" in data


def test_reset_missing_key_returns_1(tmp_path):
    rc = cmd_escalation_reset(_args(tmp_path, key="ghost"))
    assert rc == 1
