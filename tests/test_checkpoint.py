"""Tests for pipewatch.checkpoint."""

import json
import os
import pytest

from pipewatch.checkpoint import (
    Checkpoint,
    clear_checkpoints,
    from_dict,
    get_checkpoint,
    load_checkpoints,
    save_checkpoint,
    to_dict,
)


@pytest.fixture
def cp_path(tmp_path):
    return str(tmp_path / "checkpoints.json")


def _cp(**kwargs) -> Checkpoint:
    defaults = {"name": "step1", "command": "etl.py", "reached_at": "2024-01-01T00:00:00+00:00", "metadata": {}}
    defaults.update(kwargs)
    return Checkpoint(**defaults)


def test_roundtrip_dict():
    cp = _cp(metadata={"rows": "100"})
    assert from_dict(to_dict(cp)) == cp


def test_load_missing_file_returns_empty(cp_path):
    assert load_checkpoints(cp_path) == []


def test_save_and_load(cp_path):
    cp = save_checkpoint(cp_path, "step1", "etl.py")
    loaded = load_checkpoints(cp_path)
    assert len(loaded) == 1
    assert loaded[0].name == "step1"
    assert loaded[0].command == "etl.py"
    assert loaded[0].reached_at == cp.reached_at


def test_save_replaces_existing(cp_path):
    save_checkpoint(cp_path, "step1", "etl.py", {"rows": "50"})
    save_checkpoint(cp_path, "step1", "etl.py", {"rows": "100"})
    loaded = load_checkpoints(cp_path)
    assert len(loaded) == 1
    assert loaded[0].metadata["rows"] == "100"


def test_save_multiple_distinct(cp_path):
    save_checkpoint(cp_path, "step1", "etl.py")
    save_checkpoint(cp_path, "step2", "etl.py")
    loaded = load_checkpoints(cp_path)
    assert len(loaded) == 2


def test_get_checkpoint_found(cp_path):
    save_checkpoint(cp_path, "step1", "etl.py", {"x": "1"})
    cp = get_checkpoint(cp_path, "step1", "etl.py")
    assert cp is not None
    assert cp.metadata["x"] == "1"


def test_get_checkpoint_not_found(cp_path):
    assert get_checkpoint(cp_path, "missing", "etl.py") is None


def test_clear_all(cp_path):
    save_checkpoint(cp_path, "step1", "etl.py")
    save_checkpoint(cp_path, "step2", "other.py")
    removed = clear_checkpoints(cp_path)
    assert removed == 2
    assert load_checkpoints(cp_path) == []


def test_clear_by_command(cp_path):
    save_checkpoint(cp_path, "step1", "etl.py")
    save_checkpoint(cp_path, "step1", "other.py")
    removed = clear_checkpoints(cp_path, command="etl.py")
    assert removed == 1
    remaining = load_checkpoints(cp_path)
    assert len(remaining) == 1
    assert remaining[0].command == "other.py"
