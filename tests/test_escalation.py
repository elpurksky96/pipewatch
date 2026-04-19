"""Tests for pipewatch.escalation."""
import pytest
from pathlib import Path
from pipewatch.escalation import (
    EscalationState,
    load_state,
    save_state,
    record_failure,
    record_success,
    should_escalate,
    mark_escalated,
)


@pytest.fixture
def state_path(tmp_path):
    return tmp_path / "esc.json"


def test_initial_state_is_zero(state_path):
    s = load_state("myjob", state_path)
    assert s.consecutive_failures == 0
    assert s.escalated is False
    assert s.last_failure_ts is None


def test_record_failure_increments(state_path):
    record_failure("myjob", state_path)
    record_failure("myjob", state_path)
    s = load_state("myjob", state_path)
    assert s.consecutive_failures == 2


def test_record_success_resets(state_path):
    record_failure("myjob", state_path)
    record_failure("myjob", state_path)
    record_success("myjob", state_path)
    s = load_state("myjob", state_path)
    assert s.consecutive_failures == 0
    assert s.escalated is False


def test_should_escalate_at_threshold(state_path):
    record_failure("myjob", state_path)
    record_failure("myjob", state_path)
    record_failure("myjob", state_path)
    s = load_state("myjob", state_path)
    assert should_escalate(s, threshold=3) is True


def test_should_not_escalate_below_threshold(state_path):
    record_failure("myjob", state_path)
    s = load_state("myjob", state_path)
    assert should_escalate(s, threshold=3) is False


def test_mark_escalated(state_path):
    record_failure("myjob", state_path)
    mark_escalated("myjob", state_path)
    s = load_state("myjob", state_path)
    assert s.escalated is True


def test_multiple_keys_independent(state_path):
    record_failure("job_a", state_path)
    record_failure("job_a", state_path)
    record_failure("job_b", state_path)
    a = load_state("job_a", state_path)
    b = load_state("job_b", state_path)
    assert a.consecutive_failures == 2
    assert b.consecutive_failures == 1


def test_last_failure_ts_set(state_path):
    record_failure("myjob", state_path)
    s = load_state("myjob", state_path)
    assert s.last_failure_ts is not None
    assert s.last_failure_ts > 0
