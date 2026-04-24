"""Tests for pipewatch.quota."""

import time
from pathlib import Path

import pytest

from pipewatch.quota import (
    QuotaRule,
    current_count,
    find_rule,
    is_quota_exceeded,
    parse_quota_rules,
    record_run,
)


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "quota_state.json"


def _rule(max_runs: int = 3, window: int = 60) -> QuotaRule:
    return QuotaRule(command="etl:run", max_runs=max_runs, window_seconds=window)


def test_not_exceeded_initially(state_path: Path) -> None:
    assert is_quota_exceeded(_rule(), state_path) is False


def test_count_zero_initially(state_path: Path) -> None:
    assert current_count(_rule(), state_path) == 0


def test_record_increments_count(state_path: Path) -> None:
    rule = _rule()
    record_run(rule, state_path)
    record_run(rule, state_path)
    assert current_count(rule, state_path) == 2


def test_exceeded_after_max_runs(state_path: Path) -> None:
    rule = _rule(max_runs=2)
    record_run(rule, state_path)
    record_run(rule, state_path)
    assert is_quota_exceeded(rule, state_path) is True


def test_not_exceeded_below_max(state_path: Path) -> None:
    rule = _rule(max_runs=3)
    record_run(rule, state_path)
    record_run(rule, state_path)
    assert is_quota_exceeded(rule, state_path) is False


def test_old_runs_pruned(state_path: Path) -> None:
    rule = _rule(max_runs=2, window=10)
    old_time = time.time() - 20
    record_run(rule, state_path, now=old_time)
    record_run(rule, state_path, now=old_time)
    # Both timestamps are outside the window; should not be exceeded now
    assert is_quota_exceeded(rule, state_path) is False
    assert current_count(rule, state_path) == 0


def test_different_commands_are_independent(state_path: Path) -> None:
    r1 = QuotaRule(command="job:a", max_runs=1, window_seconds=60)
    r2 = QuotaRule(command="job:b", max_runs=1, window_seconds=60)
    record_run(r1, state_path)
    assert is_quota_exceeded(r1, state_path) is True
    assert is_quota_exceeded(r2, state_path) is False


def test_parse_quota_rules_basic() -> None:
    raw = [{"command": "etl:run", "max_runs": 5, "window_seconds": 3600}]
    rules = parse_quota_rules(raw)
    assert len(rules) == 1
    assert rules[0].max_runs == 5
    assert rules[0].window_seconds == 3600


def test_parse_quota_rules_default_window() -> None:
    raw = [{"command": "etl:run", "max_runs": 2}]
    rules = parse_quota_rules(raw)
    assert rules[0].window_seconds == 3600


def test_find_rule_found() -> None:
    rules = [QuotaRule("a", 1, 60), QuotaRule("b", 2, 120)]
    assert find_rule(rules, "b") is rules[1]


def test_find_rule_missing() -> None:
    rules = [QuotaRule("a", 1, 60)]
    assert find_rule(rules, "z") is None
