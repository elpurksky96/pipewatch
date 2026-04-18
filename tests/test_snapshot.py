"""Tests for snapshot.py."""
import json
import os
import pytest
from pipewatch.snapshot import (
    Snapshot, from_dict, to_dict, load_snapshots, save_snapshot,
    diff_snapshots, latest_snapshot,
)


def _snap(label="test", success_rate=1.0, avg_duration=2.5,
          total_runs=10, timeout_count=0):
    return Snapshot(
        label=label,
        timestamp="2024-01-01T00:00:00+00:00",
        success_rate=success_rate,
        avg_duration=avg_duration,
        total_runs=total_runs,
        timeout_count=timeout_count,
    )


def test_roundtrip_dict():
    s = _snap()
    assert from_dict(to_dict(s)) == s


def test_load_missing_file(tmp_path):
    assert load_snapshots(str(tmp_path / "missing.json")) == []


def test_save_and_load(tmp_path):
    path = str(tmp_path / "snaps.json")
    s = _snap()
    save_snapshot(path, s)
    loaded = load_snapshots(path)
    assert len(loaded) == 1
    assert loaded[0] == s


def test_save_appends(tmp_path):
    path = str(tmp_path / "snaps.json")
    save_snapshot(path, _snap(label="a"))
    save_snapshot(path, _snap(label="b"))
    loaded = load_snapshots(path)
    assert len(loaded) == 2
    assert loaded[1].label == "b"


def test_diff_no_change():
    s = _snap()
    assert diff_snapshots(s, s) == {}


def test_diff_detects_changes():
    old = _snap(success_rate=0.8, avg_duration=3.0)
    new = _snap(success_rate=0.9, avg_duration=2.0)
    d = diff_snapshots(old, new)
    assert "success_rate" in d
    assert d["success_rate"] == (0.8, 0.9)
    assert "avg_duration" in d


def test_latest_snapshot_none(tmp_path):
    assert latest_snapshot(str(tmp_path / "x.json")) is None


def test_latest_snapshot_returns_last(tmp_path):
    path = str(tmp_path / "snaps.json")
    save_snapshot(path, _snap(label="first"))
    save_snapshot(path, _snap(label="last"))
    assert latest_snapshot(path).label == "last"
