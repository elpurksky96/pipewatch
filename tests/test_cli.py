"""Tests for the CLI entry point."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from pipewatch.cli import build_parser, main
from pipewatch.runner import RunResult
from pipewatch.watcher import WatchResult


def _make_watch_result(success=True, timed_out=False, duration=1.0, stderr=""):
    run = RunResult(
        command=["echo", "hi"],
        returncode=0 if success else 1,
        stdout="",
        stderr=stderr,
        duration=duration,
        timed_out=timed_out,
    )
    return WatchResult(run_result=run)


def test_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["echo", "hello"])
    assert args.config == Path("pipewatch.toml")
    assert args.timeout is None
    assert args.slack_webhook is None


def test_no_command_returns_1():
    assert main([]) == 1


@patch("pipewatch.cli.watch")
@patch("pipewatch.cli.load_config", side_effect=FileNotFoundError)
def test_main_success(mock_load, mock_watch):
    mock_watch.return_value = _make_watch_result(success=True)
    result = main(["echo", "hello"])
    assert result == 0
    mock_watch.assert_called_once()


@patch("pipewatch.cli.watch")
@patch("pipewatch.cli.load_config", side_effect=FileNotFoundError)
def test_main_failure(mock_load, mock_watch):
    mock_watch.return_value = _make_watch_result(success=False)
    result = main(["false"])
    assert result == 1


@patch("pipewatch.cli.send_slack_alert")
@patch("pipewatch.cli.watch")
@patch("pipewatch.cli.load_config", side_effect=FileNotFoundError)
def test_slack_called_when_webhook_provided(mock_load, mock_watch, mock_alert):
    mock_watch.return_value = _make_watch_result(success=False)
    main(["--slack-webhook", "https://hooks.slack.com/test", "false"])
    mock_alert.assert_called_once()


@patch("pipewatch.cli.send_slack_alert")
@patch("pipewatch.cli.watch")
@patch("pipewatch.cli.load_config", side_effect=FileNotFoundError)
def test_slack_not_called_without_webhook(mock_load, mock_watch, mock_alert):
    mock_watch.return_value = _make_watch_result(success=True)
    main(["echo", "hi"])
    mock_alert.assert_not_called()


@patch("pipewatch.cli.watch")
@patch("pipewatch.cli.load_config", side_effect=FileNotFoundError)
def test_timeout_override(mock_load, mock_watch):
    mock_watch.return_value = _make_watch_result()
    main(["--timeout", "30", "sleep", "1"])
    _, call_config = mock_watch.call_args[0]
    assert call_config.timeout == 30.0
