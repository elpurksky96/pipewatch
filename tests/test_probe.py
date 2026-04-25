"""Tests for pipewatch.probe and pipewatch.probe_cmd."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pytest

from pipewatch.probe import (
    ProbeEntry,
    check_probe,
    from_dict,
    list_probes,
    load_probe,
    record_probe,
    to_dict,
)
from pipewatch.probe_cmd import cmd_probe_check, cmd_probe_list, cmd_probe_record


@pytest.fixture()
def probe_path(tmp_path: Path) -> str:
    return str(tmp_path / "probes.json")


# ---------------------------------------------------------------------------
# Unit tests for probe.py
# ---------------------------------------------------------------------------

def test_roundtrip_dict():
    e = ProbeEntry(command="etl", last_seen="2024-01-01T00:00:00+00:00", success=True, tags=["prod"])
    assert from_dict(to_dict(e)) == e


def test_record_creates_entry(probe_path):
    entry = record_probe(probe_path, "my-job", success=True)
    assert entry.command == "my-job"
    assert entry.success is True
    raw = json.loads(Path(probe_path).read_text())
    assert "my-job" in raw


def test_record_overwrites_previous(probe_path):
    record_probe(probe_path, "job", success=False)
    record_probe(probe_path, "job", success=True)
    entry = load_probe(probe_path, "job")
    assert entry is not None
    assert entry.success is True


def test_load_probe_missing_file_returns_none(probe_path):
    assert load_probe(probe_path, "ghost") is None


def test_check_probe_fresh(probe_path):
    record_probe(probe_path, "fast", success=True)
    assert check_probe(probe_path, "fast", max_age_seconds=60) is True


def test_check_probe_stale(probe_path):
    # Manually write an old timestamp
    data = {"old-job": {"command": "old-job", "last_seen": "2000-01-01T00:00:00+00:00", "success": True, "tags": []}}
    Path(probe_path).write_text(json.dumps(data))
    assert check_probe(probe_path, "old-job", max_age_seconds=60) is False


def test_check_probe_missing_command(probe_path):
    assert check_probe(probe_path, "nonexistent", max_age_seconds=60) is False


def test_list_probes_empty(probe_path):
    assert list_probes(probe_path) == []


def test_list_probes_returns_all(probe_path):
    record_probe(probe_path, "a", success=True)
    record_probe(probe_path, "b", success=False)
    entries = list_probes(probe_path)
    assert {e.command for e in entries} == {"a", "b"}


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------

def _args(**kwargs) -> argparse.Namespace:
    defaults = {"probe_file": "", "command": "job", "failed": False, "tags": "", "max_age": 3600.0}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_record_success(probe_path, capsys):
    rc = cmd_probe_record(_args(probe_file=probe_path))
    assert rc == 0
    out = capsys.readouterr().out
    assert "ok" in out


def test_cmd_record_failed(probe_path, capsys):
    rc = cmd_probe_record(_args(probe_file=probe_path, failed=True))
    assert rc == 0
    entry = load_probe(probe_path, "job")
    assert entry.success is False


def test_cmd_check_alive(probe_path, capsys):
    record_probe(probe_path, "job", success=True)
    rc = cmd_probe_check(_args(probe_file=probe_path, max_age=3600.0))
    assert rc == 0


def test_cmd_check_stale(probe_path):
    data = {"job": {"command": "job", "last_seen": "2000-01-01T00:00:00+00:00", "success": True, "tags": []}}
    Path(probe_path).write_text(json.dumps(data))
    rc = cmd_probe_check(_args(probe_file=probe_path, max_age=60.0))
    assert rc == 1


def test_cmd_list_empty(probe_path, capsys):
    rc = cmd_probe_list(_args(probe_file=probe_path))
    assert rc == 0
    assert "no probes" in capsys.readouterr().out


def test_cmd_list_shows_entries(probe_path, capsys):
    record_probe(probe_path, "pipeline-x", success=True, tags=["prod"])
    rc = cmd_probe_list(_args(probe_file=probe_path))
    assert rc == 0
    assert "pipeline-x" in capsys.readouterr().out
