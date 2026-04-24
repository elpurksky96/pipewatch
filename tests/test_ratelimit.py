"""Tests for pipewatch.ratelimit."""

import time
import pytest

from pipewatch import ratelimit


@pytest.fixture()
def state_path(tmp_path):
    return str(tmp_path / "ratelimit.json")


def test_not_rate_limited_initially(state_path):
    assert ratelimit.is_rate_limited(state_path, "job:etl", 60) is False


def test_rate_limited_after_record(state_path):
    ratelimit.record_run(state_path, "job:etl")
    assert ratelimit.is_rate_limited(state_path, "job:etl", 60) is True


def test_not_rate_limited_after_interval_expires(state_path):
    ratelimit.record_run(state_path, "job:etl")
    # Manually backdate the timestamp
    state = ratelimit._load(state_path)
    state.last_run["job:etl"] = time.time() - 120
    ratelimit._save(state_path, state)
    assert ratelimit.is_rate_limited(state_path, "job:etl", 60) is False


def test_different_keys_are_independent(state_path):
    ratelimit.record_run(state_path, "job:a")
    assert ratelimit.is_rate_limited(state_path, "job:b", 60) is False


def test_seconds_until_allowed_zero_when_not_recorded(state_path):
    assert ratelimit.seconds_until_allowed(state_path, "job:etl", 60) == 0.0


def test_seconds_until_allowed_positive_after_record(state_path):
    ratelimit.record_run(state_path, "job:etl")
    remaining = ratelimit.seconds_until_allowed(state_path, "job:etl", 60)
    assert 0 < remaining <= 60


def test_seconds_until_allowed_zero_after_interval(state_path):
    ratelimit.record_run(state_path, "job:etl")
    state = ratelimit._load(state_path)
    state.last_run["job:etl"] = time.time() - 120
    ratelimit._save(state_path, state)
    assert ratelimit.seconds_until_allowed(state_path, "job:etl", 60) == 0.0


def test_reset_specific_key(state_path):
    ratelimit.record_run(state_path, "job:a")
    ratelimit.record_run(state_path, "job:b")
    ratelimit.reset(state_path, "job:a")
    assert ratelimit.is_rate_limited(state_path, "job:a", 60) is False
    assert ratelimit.is_rate_limited(state_path, "job:b", 60) is True


def test_reset_all_keys(state_path):
    ratelimit.record_run(state_path, "job:a")
    ratelimit.record_run(state_path, "job:b")
    ratelimit.reset(state_path)
    assert ratelimit.is_rate_limited(state_path, "job:a", 60) is False
    assert ratelimit.is_rate_limited(state_path, "job:b", 60) is False


def test_describe_returns_elapsed(state_path):
    ratelimit.record_run(state_path, "job:etl")
    info = ratelimit.describe(state_path)
    assert "job:etl" in info
    assert info["job:etl"] >= 0.0


def test_describe_empty_when_no_runs(state_path):
    assert ratelimit.describe(state_path) == {}
