"""Tests for pipewatch.throttle."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from pipewatch.throttle import (
    is_throttled,
    maybe_send,
    record_alert,
)


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "throttle.json"


def test_not_throttled_initially(state_path):
    assert is_throttled("job-a", state_path=state_path) is False


def test_throttled_after_record(state_path):
    record_alert("job-a", state_path=state_path)
    assert is_throttled("job-a", cooldown=3600, state_path=state_path) is True


def test_not_throttled_after_cooldown_expires(state_path, monkeypatch):
    record_alert("job-a", state_path=state_path)
    # Advance time beyond cooldown
    monkeypatch.setattr("pipewatch.throttle.time.time", lambda: time.time() + 7200)
    assert is_throttled("job-a", cooldown=3600, state_path=state_path) is False


def test_different_keys_independent(state_path):
    record_alert("job-a", state_path=state_path)
    assert is_throttled("job-b", state_path=state_path) is False


def test_maybe_send_calls_fn_when_not_throttled(state_path):
    called = []
    sent = maybe_send("job-a", lambda: called.append(1), state_path=state_path)
    assert sent is True
    assert called == [1]


def test_maybe_send_suppresses_when_throttled(state_path):
    called = []
    record_alert("job-a", state_path=state_path)
    sent = maybe_send("job-a", lambda: called.append(1), cooldown=3600, state_path=state_path)
    assert sent is False
    assert called == []


def test_maybe_send_records_after_sending(state_path):
    maybe_send("job-x", lambda: None, state_path=state_path)
    assert is_throttled("job-x", cooldown=3600, state_path=state_path) is True


def test_missing_state_file_handled_gracefully(state_path):
    # state_path doesn't exist yet — should not raise
    assert is_throttled("job-z", state_path=state_path) is False
