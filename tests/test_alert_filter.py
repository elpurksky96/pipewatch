"""Tests for pipewatch.alert_filter."""

from types import SimpleNamespace
import pytest
from pipewatch.alert_filter import (
    AlertFilter,
    parse_alert_filter,
    should_alert,
    describe_filter,
)
from pipewatch.label import LabelSet


def _entry(success=True, timed_out=False, duration=1.0, labels=None):
    return SimpleNamespace(
        success=success,
        timed_out=timed_out,
        duration=duration,
        labels=LabelSet(labels or {}),
    )


def test_no_filter_always_alerts():
    f = AlertFilter()
    assert should_alert(_entry(), f) is True


def test_only_on_failure_blocks_success():
    f = parse_alert_filter(only_on_failure=True)
    assert should_alert(_entry(success=True), f) is False


def test_only_on_failure_passes_failure():
    f = parse_alert_filter(only_on_failure=True)
    assert should_alert(_entry(success=False), f) is True


def test_only_on_timeout_blocks_non_timeout():
    f = parse_alert_filter(only_on_timeout=True)
    assert should_alert(_entry(timed_out=False), f) is False


def test_only_on_timeout_passes_timeout():
    f = parse_alert_filter(only_on_timeout=True)
    assert should_alert(_entry(timed_out=True), f) is True


def test_min_duration_blocks_fast_entry():
    f = parse_alert_filter(min_duration=5.0)
    assert should_alert(_entry(duration=2.0), f) is False


def test_min_duration_passes_slow_entry():
    f = parse_alert_filter(min_duration=5.0)
    assert should_alert(_entry(duration=10.0), f) is True


def test_label_filter_blocks_mismatch():
    f = parse_alert_filter(labels="env=prod")
    assert should_alert(_entry(labels={"env": "staging"}), f) is False


def test_label_filter_passes_match():
    f = parse_alert_filter(labels="env=prod")
    assert should_alert(_entry(labels={"env": "prod"}), f) is True


def test_describe_filter_no_filters():
    assert describe_filter(AlertFilter()) == "no filters"


def test_describe_filter_combined():
    f = parse_alert_filter(only_on_failure=True, min_duration=3.0, labels="team=data")
    desc = describe_filter(f)
    assert "failures only" in desc
    assert "duration >= 3.0s" in desc
    assert "team=data" in desc
