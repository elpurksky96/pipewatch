"""Tests for pipewatch.alert."""

from unittest.mock import patch, MagicMock
from pipewatch.runner import RunResult
from pipewatch.alert import send_slack_alert, _build_payload


def _make_result(returncode=0, stderr="", stdout="", timed_out=False, duration=1.0):
    return RunResult(
        command="echo hi",
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=duration,
        timed_out=timed_out,
    )


def test_build_payload_success():
    payload = _build_payload(_make_result(), "myjob")
    assert "SUCCESS" in payload["text"]
    assert "myjob" in payload["text"]


def test_build_payload_failure_includes_stderr():
    payload = _build_payload(_make_result(returncode=1, stderr="boom"), "job")
    assert "FAILED" in payload["text"]
    assert "boom" in payload["text"]


def test_build_payload_timeout():
    payload = _build_payload(_make_result(timed_out=True), "job")
    assert "TIMED OUT" in payload["text"]


def test_no_alert_on_success_when_only_on_failure():
    result = _make_result(returncode=0)
    sent = send_slack_alert("http://example.com/hook", result, only_on_failure=True)
    assert sent is False


def test_alert_sent_on_failure():
    result = _make_result(returncode=1)
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_cm)
    mock_cm.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_cm):
        sent = send_slack_alert("http://example.com/hook", result, only_on_failure=True)
    assert sent is True


def test_alert_returns_false_on_network_error():
    import urllib.error
    result = _make_result(returncode=1)
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
        sent = send_slack_alert("http://example.com/hook", result)
    assert sent is False
