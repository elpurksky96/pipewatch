"""High-level notification dispatcher combining retry results and Slack alerts."""
from __future__ import annotations

from pipewatch.retry import RetryResult
from pipewatch.alert import send_slack_alert
from pipewatch.config import PipewatchConfig
from pipewatch.format import format_summary


def _build_retry_context(retry_result: RetryResult) -> str:
    """Return a short string describing retry attempts for inclusion in alerts."""
    if retry_result.attempts == 1:
        return ""
    return f"(attempt {retry_result.attempts}/{len(retry_result.all_results)})"


def notify(
    retry_result: RetryResult,
    command: str,
    config: PipewatchConfig,
) -> bool:
    """Send a Slack alert based on a RetryResult.  Returns True if alert was sent."""
    if not config.slack_webhook_url:
        return False

    run = retry_result.final
    context = _build_retry_context(retry_result)
    label = f"{command} {context}".strip()

    return send_slack_alert(
        result=run,
        webhook_url=config.slack_webhook_url,
        command=label,
        only_on_failure=config.alert_only_on_failure,
    )


def print_retry_summary(retry_result: RetryResult, command: str) -> None:
    """Print a human-readable summary including retry information."""
    run = retry_result.final
    summary = format_summary(run, command)
    if retry_result.attempts > 1:
        print(f"{summary}  [retried {retry_result.attempts - 1}x]")
    else:
        print(summary)
