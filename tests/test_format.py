"""Tests for pipewatch.format helpers."""
import pytest
from pipewatch.runner import RunResult
from pipewatch.format import (
    format_duration,
    format_status,
    truncate_stderr,
    format_summary,
)


def _result(success=True, timed_out=False, returncode=0, stderr="", duration=5.0):
    return RunResult(
        command=["my-pipeline"],
        returncode=returncode,
        stdout="",
        stderr=stderr,
        duration=duration,
        timed_out=timed_out,
    )


@pytest.mark.parametrize("seconds,expected", [
    (0.5, "0.5s"),
    (59.9, "59.9s"),
    (60, "1m 0s"),
    (90, "1m 30s"),
    (3661, "1h 1m 1s"),
])
def test_format_duration(seconds, expected):
    assert format_duration(seconds) == expected


def test_format_status_success():
    assert format_status(_result(success=True)) == "succeeded"


def test_format_status_failure():
    assert format_status(_result(success=False, returncode=2)) == "failed (exit 2)"


def test_format_status_timed_out():
    assert format_status(_result(timed_out=True)) == "timed out"


def test_truncate_stderr_short():
    text = "line1\nline2"
    assert truncate_stderr(text) == text


def test_truncate_stderr_long():
    lines = [f"line{i}" for i in range(30)]
    text = "\n".join(lines)
    result = truncate_stderr(text, max_lines=5)
    assert "omitted" in result
    assert "line29" in result
    assert "line0" not in result


def test_truncate_stderr_empty():
    assert truncate_stderr("") == ""


def test_format_summary_contains_key_fields():
    r = _result(success=False, returncode=1, stderr="err\n", duration=125.0)
    summary = format_summary(r)
    assert "my-pipeline" in summary
    assert "failed" in summary
    assert "2m 5s" in summary
    assert "err" in summary
