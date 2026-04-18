"""Tests for pipewatch.retry."""
from unittest.mock import patch, MagicMock

import pytest

from pipewatch.runner import RunResult
from pipewatch.retry import RetryConfig, RetryResult, run_with_retry


def _ok(duration=0.1):
    return RunResult(exit_code=0, stdout="ok", stderr="", duration=duration, timed_out=False)


def _fail(duration=0.1):
    return RunResult(exit_code=1, stdout="", stderr="err", duration=duration, timed_out=False)


def _timeout(duration=5.0):
    return RunResult(exit_code=1, stdout="", stderr="", duration=duration, timed_out=True)


def test_success_on_first_attempt():
    cfg = RetryConfig(max_attempts=3, delay_seconds=0)
    with patch("pipewatch.retry.run_command", return_value=_ok()) as mock_run:
        result = run_with_retry("echo hi", cfg, sleep_fn=lambda _: None)
    assert result.succeeded
    assert result.attempts == 1
    mock_run.assert_called_once()


def test_retries_on_failure_then_succeeds():
    cfg = RetryConfig(max_attempts=3, delay_seconds=1)
    side_effects = [_fail(), _fail(), _ok()]
    slept = []
    with patch("pipewatch.retry.run_command", side_effect=side_effects):
        result = run_with_retry("cmd", cfg, sleep_fn=slept.append)
    assert result.succeeded
    assert result.attempts == 3
    assert len(slept) == 2


def test_exhausts_all_attempts():
    cfg = RetryConfig(max_attempts=3, delay_seconds=0)
    with patch("pipewatch.retry.run_command", return_value=_fail()):
        result = run_with_retry("bad", cfg, sleep_fn=lambda _: None)
    assert not result.succeeded
    assert result.attempts == 3
    assert len(result.all_results) == 3


def test_no_retry_on_timeout():
    cfg = RetryConfig(max_attempts=3, delay_seconds=0)
    with patch("pipewatch.retry.run_command", return_value=_timeout()) as mock_run:
        result = run_with_retry("slow", cfg, sleep_fn=lambda _: None)
    assert result.attempts == 1
    assert result.final.timed_out
    mock_run.assert_called_once()


def test_backoff_factor_increases_delay():
    cfg = RetryConfig(max_attempts=3, delay_seconds=2.0, backoff_factor=2.0)
    slept = []
    with patch("pipewatch.retry.run_command", return_value=_fail()):
        run_with_retry("cmd", cfg, sleep_fn=slept.append)
    assert slept == [2.0, 4.0]


def test_retry_result_all_results_length():
    cfg = RetryConfig(max_attempts=2, delay_seconds=0)
    with patch("pipewatch.retry.run_command", side_effect=[_fail(), _ok()]):
        result = run_with_retry("cmd", cfg, sleep_fn=lambda _: None)
    assert len(result.all_results) == 2
