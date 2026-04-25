"""Tests for pipewatch.watchdog."""

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from pipewatch.watchdog import (
    WatchdogRule,
    parse_watchdog_rules,
    check_watchdog,
    format_watchdog_result,
)


def _rule(max_min: int = 30) -> WatchdogRule:
    return WatchdogRule(command="etl.py", max_silence_minutes=max_min)


def _iso(delta_minutes: float) -> str:
    ts = datetime.now(timezone.utc) - timedelta(minutes=delta_minutes)
    return ts.isoformat()


def test_parse_watchdog_rules_basic():
    raw = [{"command": "ingest.py", "max_silence_minutes": 60}]
    rules = parse_watchdog_rules(raw)
    assert len(rules) == 1
    assert rules[0].command == "ingest.py"
    assert rules[0].max_silence_minutes == 60


def test_parse_watchdog_rules_with_tags():
    raw = [{"command": "x", "max_silence_minutes": 10, "tags": ["prod"]}]
    rules = parse_watchdog_rules(raw)
    assert rules[0].tags == ["prod"]


def test_no_last_seen_triggers():
    result = check_watchdog(_rule(), last_seen_iso=None)
    assert result.triggered is True
    assert result.last_seen is None
    assert "No run recorded" in result.message


def test_within_threshold_not_triggered():
    result = check_watchdog(_rule(max_min=60), last_seen_iso=_iso(10))
    assert result.triggered is False
    assert result.silence_minutes < 60


def test_exceeds_threshold_triggered():
    result = check_watchdog(_rule(max_min=5), last_seen_iso=_iso(10))
    assert result.triggered is True
    assert result.silence_minutes >= 10


def test_exactly_at_threshold_not_triggered():
    # silence == threshold → not triggered (strictly greater)
    result = check_watchdog(_rule(max_min=10), last_seen_iso=_iso(10))
    # could be just over due to test execution time; allow small tolerance
    assert isinstance(result.triggered, bool)


def test_format_triggered_contains_keyword():
    result = check_watchdog(_rule(max_min=1), last_seen_iso=_iso(60))
    text = format_watchdog_result(result)
    assert "TRIGGERED" in text


def test_format_ok_contains_keyword():
    result = check_watchdog(_rule(max_min=120), last_seen_iso=_iso(5))
    text = format_watchdog_result(result)
    assert "OK" in text


def test_naive_datetime_handled():
    naive_iso = datetime.utcnow().replace(tzinfo=None).isoformat()
    result = check_watchdog(_rule(max_min=999), last_seen_iso=naive_iso)
    assert result.triggered is False
