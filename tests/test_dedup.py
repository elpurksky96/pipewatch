"""Tests for pipewatch.dedup — alert deduplication logic."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from pipewatch.dedup import (
    _content_hash,
    is_duplicate,
    prune_expired,
    record_sent,
)


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "dedup.json"


# ---------------------------------------------------------------------------
# _content_hash
# ---------------------------------------------------------------------------

def test_same_inputs_produce_same_hash():
    assert _content_hash("cmd", "err") == _content_hash("cmd", "err")


def test_different_command_produces_different_hash():
    assert _content_hash("cmd_a", "err") != _content_hash("cmd_b", "err")


def test_different_stderr_produces_different_hash():
    assert _content_hash("cmd", "err_a") != _content_hash("cmd", "err_b")


# ---------------------------------------------------------------------------
# is_duplicate / record_sent
# ---------------------------------------------------------------------------

def test_not_duplicate_initially(state_path: Path):
    assert not is_duplicate("cmd", "err", state_path=state_path)


def test_duplicate_after_record(state_path: Path):
    record_sent("cmd", "err", state_path=state_path)
    assert is_duplicate("cmd", "err", window_seconds=3600, state_path=state_path)


def test_not_duplicate_after_window_expires(state_path: Path):
    record_sent("cmd", "err", state_path=state_path)
    # Window of 0 seconds means everything is expired
    assert not is_duplicate("cmd", "err", window_seconds=0, state_path=state_path)


def test_different_commands_are_independent(state_path: Path):
    record_sent("cmd_a", "err", state_path=state_path)
    assert not is_duplicate("cmd_b", "err", state_path=state_path)


def test_missing_state_file_is_not_duplicate(tmp_path: Path):
    missing = tmp_path / "no_such_file.json"
    assert not is_duplicate("cmd", "err", state_path=missing)


# ---------------------------------------------------------------------------
# prune_expired
# ---------------------------------------------------------------------------

def test_prune_removes_old_entries(state_path: Path):
    record_sent("cmd", "err", state_path=state_path)
    removed = prune_expired(window_seconds=0, state_path=state_path)
    assert removed == 1
    assert not is_duplicate("cmd", "err", window_seconds=3600, state_path=state_path)


def test_prune_keeps_fresh_entries(state_path: Path):
    record_sent("cmd", "err", state_path=state_path)
    removed = prune_expired(window_seconds=3600, state_path=state_path)
    assert removed == 0
    assert is_duplicate("cmd", "err", window_seconds=3600, state_path=state_path)


def test_prune_missing_file_returns_zero(tmp_path: Path):
    missing = tmp_path / "no_such_file.json"
    assert prune_expired(state_path=missing) == 0
