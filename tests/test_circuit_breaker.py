"""Tests for pipewatch.circuit_breaker."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from pipewatch.circuit_breaker import (
    CircuitState,
    load_state,
    record_outcome,
    reset_circuit,
    save_state,
)


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "cb.json"


def test_initial_state_is_closed(state_path):
    s = load_state("cmd", state_path)
    assert s.consecutive_failures == 0
    assert s.tripped_at is None
    assert not s.is_open()


def test_failure_increments_count(state_path):
    record_outcome("cmd", success=False, threshold=5, path=state_path)
    s = load_state("cmd", state_path)
    assert s.consecutive_failures == 1
    assert s.tripped_at is None


def test_circuit_trips_at_threshold(state_path):
    for _ in range(3):
        record_outcome("cmd", success=False, threshold=3, path=state_path)
    s = load_state("cmd", state_path)
    assert s.consecutive_failures == 3
    assert s.tripped_at is not None
    assert s.is_open()


def test_success_resets_failures(state_path):
    record_outcome("cmd", success=False, threshold=3, path=state_path)
    record_outcome("cmd", success=True, threshold=3, path=state_path)
    s = load_state("cmd", state_path)
    assert s.consecutive_failures == 0
    assert s.tripped_at is None


def test_manual_reset_clears_state(state_path):
    for _ in range(3):
        record_outcome("cmd", success=False, threshold=3, path=state_path)
    reset_circuit("cmd", state_path)
    s = load_state("cmd", state_path)
    assert not s.is_open()
    assert s.consecutive_failures == 0


def test_half_open_after_cooldown(state_path):
    s = CircuitState(command="cmd", consecutive_failures=3, tripped_at=time.time() - 999, reset_after=300)
    save_state(s, state_path)
    loaded = load_state("cmd", state_path)
    assert not loaded.is_open()
    assert loaded.is_half_open()


def test_different_commands_are_independent(state_path):
    for _ in range(3):
        record_outcome("cmd_a", success=False, threshold=3, path=state_path)
    sa = load_state("cmd_a", state_path)
    sb = load_state("cmd_b", state_path)
    assert sa.is_open()
    assert not sb.is_open()


def test_does_not_trip_twice(state_path):
    for _ in range(5):
        record_outcome("cmd", success=False, threshold=3, path=state_path)
    s1 = load_state("cmd", state_path)
    first_trip = s1.tripped_at
    assert first_trip is not None
    # tripped_at should remain the original timestamp
    record_outcome("cmd", success=False, threshold=3, path=state_path)
    s2 = load_state("cmd", state_path)
    assert s2.tripped_at == first_trip
