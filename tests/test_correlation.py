"""Tests for pipewatch.correlation."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from pipewatch.correlation import (
    CorrelationGroup,
    find_correlated_failures,
    format_correlation_report,
    group_by_field,
)


def _e(command: str, success: bool, duration: float = 1.0) -> SimpleNamespace:
    return SimpleNamespace(command=command, success=success, duration=duration)


def test_group_by_field_basic():
    entries = [_e("cmd_a", True), _e("cmd_a", False), _e("cmd_b", True)]
    groups = group_by_field(entries, "command")
    assert set(groups.keys()) == {"cmd_a", "cmd_b"}
    assert groups["cmd_a"].total == 2
    assert groups["cmd_b"].total == 1


def test_group_by_field_failure_count():
    entries = [_e("x", False), _e("x", False), _e("x", True)]
    groups = group_by_field(entries, "command")
    assert groups["x"].failures == 2


def test_group_by_field_avg_duration():
    entries = [_e("y", True, 2.0), _e("y", True, 4.0)]
    groups = group_by_field(entries, "command")
    assert groups["y"].avg_duration == pytest.approx(3.0)


def test_group_by_field_skips_missing_attribute():
    entries = [SimpleNamespace(other="val"), _e("z", True)]
    groups = group_by_field(entries, "command")
    assert "z" in groups
    assert len(groups) == 1


def test_find_correlated_failures_returns_above_threshold():
    entries = [_e("bad", False)] * 4 + [_e("bad", True)]
    result = find_correlated_failures(entries, "command", min_failure_rate=0.5, min_samples=2)
    assert len(result) == 1
    assert result[0].key == "bad"


def test_find_correlated_failures_excludes_below_threshold():
    entries = [_e("ok", True)] * 3 + [_e("ok", False)]
    result = find_correlated_failures(entries, "command", min_failure_rate=0.8, min_samples=2)
    assert result == []


def test_find_correlated_failures_respects_min_samples():
    entries = [_e("lone", False)]
    result = find_correlated_failures(entries, "command", min_failure_rate=0.5, min_samples=2)
    assert result == []


def test_format_correlation_report_empty():
    report = format_correlation_report([], "command")
    assert "No correlated failures" in report


def test_format_correlation_report_shows_key():
    groups = [CorrelationGroup(key="pipeline_x", total=5, failures=4, avg_duration=3.5)]
    report = format_correlation_report(groups, "command")
    assert "pipeline_x" in report
    assert "80.0%" in report


def test_format_correlation_report_sorted_by_failure_rate():
    g1 = CorrelationGroup(key="low", total=4, failures=1, avg_duration=1.0)
    g2 = CorrelationGroup(key="high", total=4, failures=3, avg_duration=1.0)
    report = format_correlation_report([g1, g2], "command")
    assert report.index("high") < report.index("low")
