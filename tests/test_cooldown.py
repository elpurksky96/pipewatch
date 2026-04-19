"""Tests for pipewatch.cooldown."""
import time
from pathlib import Path

import pytest

from pipewatch.cooldown import describe, is_in_cooldown, record_alert, reset


@pytest.fixture
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "cooldown.json"


def test_not_in_cooldown_initially(state_path):
    assert is_in_cooldown("job:etl", 300, path=state_path) is False


def test_in_cooldown_after_record(state_path):
    record_alert("job:etl", path=state_path)
    assert is_in_cooldown("job:etl", 300, path=state_path) is True


def test_not_in_cooldown_after_window_expires(state_path):
    past = time.time() - 400
    record_alert("job:etl", path=state_path, _now=past)
    assert is_in_cooldown("job:etl", 300, path=state_path) is False


def test_different_keys_independent(state_path):
    record_alert("job:a", path=state_path)
    assert is_in_cooldown("job:a", 300, path=state_path) is True
    assert is_in_cooldown("job:b", 300, path=state_path) is False


def test_reset_specific_key(state_path):
    record_alert("job:a", path=state_path)
    record_alert("job:b", path=state_path)
    reset(key="job:a", path=state_path)
    assert is_in_cooldown("job:a", 300, path=state_path) is False
    assert is_in_cooldown("job:b", 300, path=state_path) is True


def test_reset_all(state_path):
    record_alert("job:a", path=state_path)
    record_alert("job:b", path=state_path)
    reset(path=state_path)
    assert is_in_cooldown("job:a", 300, path=state_path) is False
    assert is_in_cooldown("job:b", 300, path=state_path) is False


def test_describe_empty(state_path):
    assert describe(path=state_path) == "No cooldown entries."


def test_describe_shows_entries(state_path):
    record_alert("job:etl", path=state_path)
    out = describe(path=state_path)
    assert "job:etl" in out
    assert "last alert" in out
