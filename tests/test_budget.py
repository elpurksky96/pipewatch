"""Tests for pipewatch.budget."""

import pytest
from pipewatch.budget import (
    BudgetRule,
    BudgetResult,
    check_budget,
    find_rule,
    format_budget_result,
    parse_budget_rules,
)


def _rule(max_s: float = 60.0, warn_s=None) -> BudgetRule:
    return BudgetRule(command="etl.py", max_seconds=max_s, warn_seconds=warn_s)


# --- parse_budget_rules ---

def test_parse_budget_rules_basic():
    raw = [{"command": "etl.py", "max_seconds": 120}]
    rules = parse_budget_rules(raw)
    assert len(rules) == 1
    assert rules[0].command == "etl.py"
    assert rules[0].max_seconds == 120.0
    assert rules[0].warn_seconds is None


def test_parse_budget_rules_with_warn():
    raw = [{"command": "etl.py", "max_seconds": 120, "warn_seconds": 90}]
    rules = parse_budget_rules(raw)
    assert rules[0].warn_seconds == 90.0


def test_parse_budget_rules_empty():
    assert parse_budget_rules([]) == []


# --- find_rule ---

def test_find_rule_found():
    rules = [_rule(), BudgetRule(command="other.py", max_seconds=30)]
    found = find_rule(rules, "etl.py")
    assert found is not None
    assert found.command == "etl.py"


def test_find_rule_not_found():
    rules = [_rule()]
    assert find_rule(rules, "missing.py") is None


# --- check_budget ---

def test_check_budget_within_limit():
    rule = _rule(max_s=60.0)
    result = check_budget(rule, 30.0)
    assert not result.exceeded
    assert not result.warned
    assert result.overage == 0.0


def test_check_budget_exceeded():
    rule = _rule(max_s=60.0)
    result = check_budget(rule, 75.0)
    assert result.exceeded
    assert not result.warned
    assert result.overage == pytest.approx(15.0)


def test_check_budget_warn_zone():
    rule = _rule(max_s=60.0, warn_s=45.0)
    result = check_budget(rule, 50.0)
    assert not result.exceeded
    assert result.warned
    assert result.overage == 0.0


def test_check_budget_exactly_at_limit_not_exceeded():
    rule = _rule(max_s=60.0)
    result = check_budget(rule, 60.0)
    assert not result.exceeded


# --- format_budget_result ---

def test_format_budget_result_ok():
    rule = _rule(max_s=60.0)
    result = check_budget(rule, 30.0)
    msg = format_budget_result(result)
    assert "BUDGET OK" in msg
    assert "etl.py" in msg


def test_format_budget_result_exceeded():
    rule = _rule(max_s=60.0)
    result = check_budget(rule, 90.0)
    msg = format_budget_result(result)
    assert "BUDGET EXCEEDED" in msg
    assert "+30.0s" in msg


def test_format_budget_result_warned():
    rule = _rule(max_s=60.0, warn_s=40.0)
    result = check_budget(rule, 50.0)
    msg = format_budget_result(result)
    assert "BUDGET WARNING" in msg
