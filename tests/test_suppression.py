"""Tests for pipewatch.suppression."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from pipewatch.suppression import (
    SuppressionWindow,
    load_windows,
    save_windows,
    is_suppressed,
    describe_window,
)


def _win(
    name="maint",
    offset_start=-1,
    offset_end=1,
    commands=None,
    reason="",
) -> SuppressionWindow:
    now = datetime.now(timezone.utc)
    start = (now + timedelta(hours=offset_start)).isoformat()
    end = (now + timedelta(hours=offset_end)).isoformat()
    return SuppressionWindow(
        name=name,
        start_iso=start,
        end_iso=end,
        commands=commands or [],
        reason=reason,
    )


def test_roundtrip_dict():
    w = _win(commands=["etl"], reason="scheduled")
    assert SuppressionWindow.from_dict(w.to_dict()).name == w.name
    assert SuppressionWindow.from_dict(w.to_dict()).commands == ["etl"]


def test_is_active_within_window():
    w = _win(offset_start=-1, offset_end=1)
    assert w.is_active() is True


def test_is_active_before_window():
    w = _win(offset_start=1, offset_end=2)
    assert w.is_active() is False


def test_is_active_after_window():
    w = _win(offset_start=-3, offset_end=-1)
    assert w.is_active() is False


def test_covers_command_empty_matches_all():
    w = _win(commands=[])
    assert w.covers_command("anything") is True


def test_covers_command_specific():
    w = _win(commands=["etl"])
    assert w.covers_command("etl") is True
    assert w.covers_command("other") is False


def test_is_suppressed_returns_window(tmp_path):
    w = _win()
    result = is_suppressed("etl", [w])
    assert result is w


def test_is_suppressed_returns_none_when_inactive(tmp_path):
    w = _win(offset_start=1, offset_end=2)
    assert is_suppressed("etl", [w]) is None


def test_is_suppressed_returns_none_when_command_not_covered():
    w = _win(commands=["other"])
    assert is_suppressed("etl", [w]) is None


def test_load_windows_missing_file(tmp_path):
    assert load_windows(tmp_path / "nope.json") == []


def test_save_and_load_roundtrip(tmp_path):
    p = tmp_path / "windows.json"
    windows = [_win(name="w1"), _win(name="w2", commands=["cmd"])]
    save_windows(p, windows)
    loaded = load_windows(p)
    assert len(loaded) == 2
    assert loaded[0].name == "w1"
    assert loaded[1].commands == ["cmd"]


def test_describe_window_includes_name():
    w = _win(name="deploy", reason="release", commands=["migrate"])
    desc = describe_window(w)
    assert "deploy" in desc
    assert "release" in desc
    assert "migrate" in desc


def test_describe_window_all_commands():
    w = _win(commands=[])
    assert "all" in describe_window(w)
