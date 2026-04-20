"""Tests for pipewatch.checkpoint_cmd."""

import argparse
import pytest

from pipewatch.checkpoint import save_checkpoint
from pipewatch.checkpoint_cmd import (
    cmd_checkpoint_clear,
    cmd_checkpoint_get,
    cmd_checkpoint_list,
    cmd_checkpoint_set,
    dispatch,
)


def _args(cp_path, **kwargs) -> argparse.Namespace:
    defaults = {
        "checkpoint_path": cp_path,
        "name": "step1",
        "command": "etl.py",
        "meta": None,
        "checkpoint_action": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def cp_path(tmp_path):
    return str(tmp_path / "checkpoints.json")


def test_cmd_set_creates_checkpoint(cp_path):
    args = _args(cp_path, meta=["rows=42"])
    rc = cmd_checkpoint_set(args)
    assert rc == 0


def test_cmd_set_parses_meta(cp_path, capsys):
    args = _args(cp_path, meta=["env=prod", "rows=10"])
    cmd_checkpoint_set(args)
    from pipewatch.checkpoint import get_checkpoint
    cp = get_checkpoint(cp_path, "step1", "etl.py")
    assert cp is not None
    assert cp.metadata["env"] == "prod"


def test_cmd_get_found(cp_path, capsys):
    save_checkpoint(cp_path, "step1", "etl.py", {"k": "v"})
    args = _args(cp_path)
    rc = cmd_checkpoint_get(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "step1" in out
    assert "etl.py" in out


def test_cmd_get_not_found(cp_path, capsys):
    args = _args(cp_path, name="missing")
    rc = cmd_checkpoint_get(args)
    assert rc == 1
    assert "No checkpoint" in capsys.readouterr().out


def test_cmd_list_empty(cp_path, capsys):
    args = _args(cp_path)
    rc = cmd_checkpoint_list(args)
    assert rc == 0
    assert "No checkpoints" in capsys.readouterr().out


def test_cmd_list_shows_entries(cp_path, capsys):
    save_checkpoint(cp_path, "step1", "etl.py")
    args = _args(cp_path)
    cmd_checkpoint_list(args)
    out = capsys.readouterr().out
    assert "etl.py" in out
    assert "step1" in out


def test_cmd_clear_all(cp_path, capsys):
    save_checkpoint(cp_path, "step1", "etl.py")
    args = _args(cp_path, command=None)
    rc = cmd_checkpoint_clear(args)
    assert rc == 0
    assert "1" in capsys.readouterr().out


def test_dispatch_unknown_action(cp_path, capsys):
    args = _args(cp_path, checkpoint_action="unknown")
    rc = dispatch(args)
    assert rc == 1
