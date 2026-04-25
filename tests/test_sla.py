"""Tests for pipewatch.sla."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from pipewatch.sla import (
    SLARule,
    check_sla,
    find_rule,
    format_sla_result,
    parse_sla_rules,
)


def _e(success: bool, duration: float = 1.0):
    return SimpleNamespace(success=success, duration=duration)


# ---------------------------------------------------------------------------
# parse_sla_rules
# ---------------------------------------------------------------------------

def test_parse_sla_rules_basic():
    raw = [{"command": "etl", "min_success_rate": 0.9, "max_duration_seconds": 30.0}]
    rules = parse_sla_rules(raw)
    assert len(rules) == 1
    assert rules[0].command == "etl"
    assert rules[0].min_success_rate == 0.9
    assert rules[0].max_duration_seconds == 30.0
    assert rules[0].window == 20  # default


def test_parse_sla_rules_custom_window():
    raw = [{"command": "sync", "window": 5}]
    rules = parse_sla_rules(raw)
    assert rules[0].window == 5


def test_parse_sla_rules_empty():
    assert parse_sla_rules([]) == []


# ---------------------------------------------------------------------------
# find_rule
# ---------------------------------------------------------------------------

def test_find_rule_found():
    rules = [SLARule(command="etl"), SLARule(command="sync")]
    assert find_rule(rules, "sync").command == "sync"


def test_find_rule_missing_returns_none():
    rules = [SLARule(command="etl")]
    assert find_rule(rules, "nope") is None


# ---------------------------------------------------------------------------
# check_sla
# ---------------------------------------------------------------------------

def test_check_sla_no_entries_passes():
    rule = SLARule(command="etl", min_success_rate=0.9)
    result = check_sla(rule, [])
    assert result.passed is True
    assert result.success_rate is None


def test_check_sla_all_pass_within_rate():
    rule = SLARule(command="etl", min_success_rate=0.8)
    entries = [_e(True)] * 10
    result = check_sla(rule, entries)
    assert result.passed is True
    assert result.success_rate == pytest.approx(1.0)
    assert result.violations == []


def test_check_sla_rate_breach():
    rule = SLARule(command="etl", min_success_rate=0.9)
    entries = [_e(True)] * 7 + [_e(False)] * 3
    result = check_sla(rule, entries)
    assert result.passed is False
    assert any("success rate" in v for v in result.violations)


def test_check_sla_duration_breach():
    rule = SLARule(command="etl", max_duration_seconds=5.0)
    entries = [_e(True, duration=10.0)] * 5
    result = check_sla(rule, entries)
    assert result.passed is False
    assert any("avg duration" in v for v in result.violations)


def test_check_sla_window_limits_entries():
    rule = SLARule(command="etl", min_success_rate=0.9, window=3)
    # First 7 entries fail, last 3 succeed — only window=3 considered
    entries = [_e(False)] * 7 + [_e(True)] * 3
    result = check_sla(rule, entries)
    assert result.passed is True


# ---------------------------------------------------------------------------
# format_sla_result
# ---------------------------------------------------------------------------

def test_format_sla_result_ok():
    rule = SLARule(command="etl", min_success_rate=0.8)
    result = check_sla(rule, [_e(True, 2.5)] * 4)
    text = format_sla_result(result)
    assert "OK" in text
    assert "etl" in text


def test_format_sla_result_breach_includes_violations():
    rule = SLARule(command="etl", min_success_rate=0.9)
    entries = [_e(False)] * 10
    result = check_sla(rule, entries)
    text = format_sla_result(result)
    assert "BREACH" in text
    assert "success rate" in text
