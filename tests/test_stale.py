"""Tests for pipewatch.stale."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from pipewatch.stale import (
    StalenessRule,
    _parse_rules,
    check_staleness,
    format_staleness,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Entry:
    def __init__(self, command: str, timestamp: str):
        self.command = command
        self.timestamp = timestamp


_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(command: str, hours_ago: float) -> _Entry:
    ts = _NOW - timedelta(hours=hours_ago)
    return _Entry(command=command, timestamp=ts.isoformat())


# ---------------------------------------------------------------------------
# _parse_rules
# ---------------------------------------------------------------------------

def test_parse_rules_basic():
    raw = [{"command": "etl", "max_gap_hours": 6}]
    rules = _parse_rules(raw)
    assert len(rules) == 1
    assert rules[0].command == "etl"
    assert rules[0].max_gap_hours == 6.0


def test_parse_rules_empty():
    assert _parse_rules([]) == []


# ---------------------------------------------------------------------------
# check_staleness
# ---------------------------------------------------------------------------

def test_not_stale_when_recent():
    rule = StalenessRule(command="etl", max_gap_hours=6)
    history = [_entry("etl", 3)]
    result = check_staleness(rule, history, now=_NOW)
    assert not result.is_stale
    assert result.hours_since == pytest.approx(3.0, abs=0.01)


def test_stale_when_too_old():
    rule = StalenessRule(command="etl", max_gap_hours=6)
    history = [_entry("etl", 10)]
    result = check_staleness(rule, history, now=_NOW)
    assert result.is_stale
    assert result.hours_since == pytest.approx(10.0, abs=0.01)


def test_stale_when_never_run():
    rule = StalenessRule(command="etl", max_gap_hours=6)
    result = check_staleness(rule, [], now=_NOW)
    assert result.is_stale
    assert result.last_run_iso is None
    assert result.hours_since is None


def test_uses_most_recent_entry():
    rule = StalenessRule(command="etl", max_gap_hours=6)
    history = [_entry("etl", 10), _entry("etl", 2)]
    result = check_staleness(rule, history, now=_NOW)
    assert not result.is_stale
    assert result.hours_since == pytest.approx(2.0, abs=0.01)


def test_ignores_other_commands():
    rule = StalenessRule(command="etl", max_gap_hours=6)
    history = [_entry("other", 1)]
    result = check_staleness(rule, history, now=_NOW)
    assert result.is_stale


# ---------------------------------------------------------------------------
# format_staleness
# ---------------------------------------------------------------------------

def test_format_ok():
    rule = StalenessRule(command="etl", max_gap_hours=6)
    result = check_staleness(rule, [_entry("etl", 3)], now=_NOW)
    text = format_staleness(result)
    assert text.startswith("[OK]")
    assert "etl" in text


def test_format_stale():
    rule = StalenessRule(command="etl", max_gap_hours=6)
    result = check_staleness(rule, [], now=_NOW)
    text = format_staleness(result)
    assert text.startswith("[STALE]")
    assert "never run" in text
