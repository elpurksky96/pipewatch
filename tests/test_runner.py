"""Tests for pipewatch.runner."""

import pytest
from pipewatch.runner import run_command, RunResult


def test_successful_command():
    result = run_command("echo hello")
    assert result.success
    assert result.returncode == 0
    assert "hello" in result.stdout
    assert result.duration_seconds >= 0


def test_failing_command():
    result = run_command("exit 1")
    assert not result.success
    assert result.returncode == 1


def test_stderr_captured():
    result = run_command("echo err >&2")
    assert "err" in result.stderr


def test_timeout_sets_timed_out():
    result = run_command("sleep 10", timeout=1)
    assert result.timed_out
    assert not result.success
    assert result.returncode == -1


def test_duration_is_positive():
    result = run_command("echo hi")
    assert result.duration_seconds > 0


def test_run_result_command_stored():
    result = run_command("echo stored")
    assert result.command == "echo stored"
