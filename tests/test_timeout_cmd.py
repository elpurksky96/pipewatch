"""Tests for pipewatch.timeout_cmd."""

import argparse
from unittest.mock import patch

import pytest

from pipewatch.timeout_cmd import cmd_timeout_check, cmd_timeout_show, dispatch
from pipewatch.timeout_policy import TimeoutPolicy


def _policy(**kwargs) -> TimeoutPolicy:
    return TimeoutPolicy(**kwargs)


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"timeout_cmd": "check", "elapsed": 50.0, "command": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_timeout_show_prints_json(capsys):
    p = _policy(default_timeout=60, overrides={"etl": 300})
    cmd_timeout_show(p)
    out = capsys.readouterr().out
    assert "default_timeout" in out
    assert "60" in out
    assert "etl" in out


def test_cmd_timeout_check_ok(capsys):
    p = _policy(default_timeout=100)
    args = _args(elapsed=40.0, command="my_cmd")
    rc = cmd_timeout_check(args, p)
    out = capsys.readouterr().out
    assert rc == 0
    assert "ok" in out


def test_cmd_timeout_check_warn(capsys):
    p = _policy(default_timeout=100, warn_at_fraction=0.8)
    args = _args(elapsed=85.0, command="my_cmd")
    rc = cmd_timeout_check(args, p)
    out = capsys.readouterr().out
    assert rc == 0
    assert "warn" in out


def test_cmd_timeout_check_exceeded_returns_1(capsys):
    p = _policy(default_timeout=100)
    args = _args(elapsed=110.0, command="my_cmd")
    rc = cmd_timeout_check(args, p)
    assert rc == 1
    out = capsys.readouterr().out
    assert "exceeded" in out


def test_dispatch_show(capsys):
    p = _policy(default_timeout=30)
    args = argparse.Namespace(timeout_cmd="show")
    rc = dispatch(args, p)
    assert rc == 0
    assert "default_timeout" in capsys.readouterr().out


def test_dispatch_unknown_returns_1(capsys):
    p = _policy()
    args = argparse.Namespace(timeout_cmd="unknown")
    rc = dispatch(args, p)
    assert rc == 1
