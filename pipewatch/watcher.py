"""Orchestrate run + alert using PipewatchConfig."""

from dataclasses import dataclass
from typing import Optional

from pipewatch.config import PipewatchConfig
from pipewatch.runner import RunResult, run_command
from pipewatch.alert import send_slack_alert


@dataclass
class WatchResult:
    run_result: RunResult
    alert_sent: bool


def watch(
    command: str,
    config: PipewatchConfig,
    job_name: Optional[str] = None,
) -> WatchResult:
    """Run *command* and send a Slack alert according to *config*."""
    name = job_name or config.job_name or command[:40]

    result = run_command(
        command,
        timeout=config.timeout_seconds,
    )

    alert_sent = False
    if config.slack_webhook_url:
        alert_sent = send_slack_alert(
            webhook_url=config.slack_webhook_url,
            result=result,
            job_name=name,
            only_on_failure=config.alert_only_on_failure,
        )

    return WatchResult(run_result=result, alert_sent=alert_sent)
