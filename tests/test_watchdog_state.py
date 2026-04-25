"""Tests for pipewatch.watchdog_state."""

import json
from pathlib import Path

import pytest

from pipewatch.watchdog_state import get_last_seen, record_seen, clear_seen, all_seen


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "watchdog_state.json"


def test_get_last_seen_missing_file_returns_none(state_path):
    assert get_last_seen("cmd", path=state_path) is None


def test_record_seen_creates_entry(state_path):
    ts = record_seen("etl.py", path=state_path)
    assert isinstance(ts, str)
    assert get_last_seen("etl.py", path=state_path) == ts


def test_record_seen_overwrites(state_path):
    ts1 = record_seen("etl.py", path=state_path)
    ts2 = record_seen("etl.py", path=state_path)
    assert get_last_seen("etl.py", path=state_path) == ts2


def test_different_commands_independent(state_path):
    record_seen("a.py", path=state_path)
    record_seen("b.py", path=state_path)
    assert get_last_seen("a.py", path=state_path) is not None
    assert get_last_seen("b.py", path=state_path) is not None


def test_clear_seen_removes_entry(state_path):
    record_seen("etl.py", path=state_path)
    removed = clear_seen("etl.py", path=state_path)
    assert removed is True
    assert get_last_seen("etl.py", path=state_path) is None


def test_clear_seen_missing_returns_false(state_path):
    assert clear_seen("ghost.py", path=state_path) is False


def test_all_seen_returns_all(state_path):
    record_seen("a.py", path=state_path)
    record_seen("b.py", path=state_path)
    entries = all_seen(path=state_path)
    assert set(entries.keys()) == {"a.py", "b.py"}


def test_all_seen_empty_when_no_file(state_path):
    assert all_seen(path=state_path) == {}


def test_state_file_is_valid_json(state_path):
    record_seen("x.py", path=state_path)
    data = json.loads(state_path.read_text())
    assert "x.py" in data
