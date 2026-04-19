"""Tests for pipewatch.window."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional

import pytest

from pipewatch.window import WindowConfig, filter_by_window, parse_window


@dataclass
class _Entry:
    name: str
    timestamp: Optional[str] = None


def _ts(delta_hours: float) -> str:
    dt = datetime.now(tz=timezone.utc) + timedelta(hours=delta_hours)
    return dt.isoformat()


# --- WindowConfig ---

def test_total_seconds_hours():
    assert WindowConfig(hours=2).total_seconds() == 7200


def test_total_seconds_days():
    assert WindowConfig(days=1).total_seconds() == 86400


def test_total_seconds_none():
    assert WindowConfig().total_seconds() is None


def test_describe_hours():
    assert WindowConfig(hours=6).describe() == "last 6.0h"


def test_describe_days():
    assert WindowConfig(days=3).describe() == "last 3.0d"


def test_describe_all_time():
    assert WindowConfig().describe() == "all time"


# --- filter_by_window ---

def test_no_window_returns_all():
    entries = [_Entry("a", _ts(-100)), _Entry("b", _ts(-1))]
    assert filter_by_window(entries, WindowConfig()) == entries


def test_recent_entries_kept():
    entries = [_Entry("recent", _ts(-0.5)), _Entry("old", _ts(-48))]
    result = filter_by_window(entries, WindowConfig(hours=24))
    assert len(result) == 1
    assert result[0].name == "recent"


def test_no_timestamp_passes_through():
    e = _Entry("no-ts")
    result = filter_by_window([e], WindowConfig(hours=1))
    assert result == [e]


def test_bad_timestamp_passes_through():
    e = _Entry("bad", timestamp="not-a-date")
    result = filter_by_window([e], WindowConfig(hours=1))
    assert result == [e]


# --- parse_window ---

def test_parse_hours():
    cfg = parse_window("12h")
    assert cfg.hours == 12.0


def test_parse_days():
    cfg = parse_window("7d")
    assert cfg.days == 7.0


def test_parse_none_returns_empty():
    cfg = parse_window(None)
    assert cfg.total_seconds() is None


def test_parse_invalid_raises():
    with pytest.raises(ValueError):
        parse_window("5m")
