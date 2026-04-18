"""Tests for pipewatch.notify."""
from unittest.mock import patch, MagicMock

import pytest

from pipewatch.runner import RunResult
from pipewatch.retry import RetryResult
from pipewatch.config import PipewatchConfig
from pipewatch.notify import notify, print_retry_summary, _build_retry_context


def _run(exit_code=0):
    return RunResult(exit_code=exit_code, stdout="", stderr="oops" if exit_code else "",
                     duration=1.0, timed_out=False)


def _retry(exit_code=0, attempts=1):
    results = [_run(1)] * (attempts - 1) + [_run(exit_code)]
    return RetryResult(final=results[-1], attempts=attempts, all_results=results)


def _cfg(webhook=None, only_on_failure=True):
    return PipewatchConfig(slack_webhook_url=webhook, alert_only_on_failure=only_on_failure)


def test_no_alert_without_webhook():
    sent = notify(_retry(), "cmd", _cfg(webhook=None))
    assert sent is False


def test_alert_sent_with_webhook():
    with patch("pipewatch.notify.send_slack_alert", return_value=True) as mock_alert:
        sent = notify(_retry(exit_code=1), "cmd", _cfg(webhook="http://hook"))
    assert sent is True
    mock_alert.assert_called_once()


def test_command_label_includes_retry_context():
    captured = {}
    def fake_alert(**kwargs):
        captured.update(kwargs)
        return True
    with patch("pipewatch.notify.send_slack_alert", side_effect=fake_alert):
        notify(_retry(exit_code=1, attempts=3), "myjob", _cfg(webhook="http://hook"))
    assert "(attempt 3/3)" in captured["command"]


def test_no_retry_context_on_first_attempt():
    assert _build_retry_context(_retry(attempts=1)) == ""


def test_retry_context_shows_attempts():
    ctx = _build_retry_context(_retry(attempts=2))
    assert "2" in ctx


def test_print_retry_summary_single(capsys):
    print_retry_summary(_retry(), "echo hi")
    out = capsys.readouterr().out
    assert "echo hi" in out
    assert "retried" not in out


def test_print_retry_summary_multi(capsys):
    print_retry_summary(_retry(attempts=3), "echo hi")
    out = capsys.readouterr().out
    assert "retried 2x" in out
