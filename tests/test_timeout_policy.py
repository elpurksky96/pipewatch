"""Tests for pipewatch.timeout_policy."""

import pytest

from pipewatch.timeout_policy import (
    TimeoutPolicy,
    classify_duration,
    parse_policy,
    policy_to_dict,
)


def _policy(**kwargs) -> TimeoutPolicy:
    return TimeoutPolicy(**kwargs)


def test_resolve_timeout_default():
    p = _policy(default_timeout=120)
    assert p.resolve_timeout("any command") == 120


def test_resolve_timeout_override_wins():
    p = _policy(default_timeout=60, overrides={"etl_job": 300})
    assert p.resolve_timeout("run etl_job now") == 300


def test_resolve_timeout_no_match_falls_back():
    p = _policy(default_timeout=60, overrides={"etl_job": 300})
    assert p.resolve_timeout("other command") == 60


def test_resolve_timeout_none_when_unset():
    p = _policy()
    assert p.resolve_timeout("anything") is None


def test_warn_threshold_fraction():
    p = _policy(default_timeout=100, warn_at_fraction=0.8)
    assert p.warn_threshold("cmd") == pytest.approx(80.0)


def test_warn_threshold_none_without_timeout():
    p = _policy(warn_at_fraction=0.8)
    assert p.warn_threshold("cmd") is None


def test_classify_ok():
    p = _policy(default_timeout=100)
    assert classify_duration(50.0, "cmd", p) == "ok"


def test_classify_warn():
    p = _policy(default_timeout=100, warn_at_fraction=0.8)
    assert classify_duration(85.0, "cmd", p) == "warn"


def test_classify_exceeded():
    p = _policy(default_timeout=100)
    assert classify_duration(105.0, "cmd", p) == "exceeded"


def test_classify_no_timeout_always_ok():
    p = _policy()
    assert classify_duration(9999.0, "cmd", p) == "ok"


def test_parse_policy_roundtrip():
    raw = {"default_timeout": 60, "overrides": {"job_a": 180}, "warn_at_fraction": 0.75}
    p = parse_policy(raw)
    assert p.default_timeout == 60
    assert p.overrides == {"job_a": 180}
    assert p.warn_at_fraction == pytest.approx(0.75)


def test_policy_to_dict_roundtrip():
    p = TimeoutPolicy(default_timeout=30, overrides={"x": 90}, warn_at_fraction=0.9)
    d = policy_to_dict(p)
    p2 = parse_policy(d)
    assert p2.default_timeout == p.default_timeout
    assert p2.overrides == p.overrides
    assert p2.warn_at_fraction == pytest.approx(p.warn_at_fraction)
