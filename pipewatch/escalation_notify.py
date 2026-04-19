"""Integrate escalation tracking with Slack notifications."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pipewatch.escalation import (
    DEFAULT_STATE_PATH,
    load_state,
    record_failure,
    record_success,
    should_escalate,
    mark_escalated,
)
from pipewatch.alert import send_slack_alert
from pipewatch.runner import RunResult


@dataclass
class EscalationConfig:
    threshold: int = 3
    webhook_url: Optional[str] = None
    state_path: Path = DEFAULT_STATE_PATH


def handle_result(
    result: RunResult,
    command: str,
    cfg: EscalationConfig,
) -> bool:
    """Update escalation state and send alert if threshold reached.
    Returns True if an escalation alert was sent.
    """
    if result.success:
        record_success(command, cfg.state_path)
        return False

    state = record_failure(command, cfg.state_path)

    if not should_escalate(state, cfg.threshold):
        return False

    already = load_state(command, cfg.state_path).escalated
    if already:
        return False

    mark_escalated(command, cfg.state_path)

    if cfg.webhook_url:
        payload = _build_escalation_payload(command, state.consecutive_failures)
        send_slack_alert(cfg.webhook_url, payload)

    return True


def _build_escalation_payload(command: str, failures: int) -> dict:
    return {
        "text": (
            f":rotating_light: *Escalation alert* for `{command}`\n"
            f"{failures} consecutive failures reached."
        )
    }


def format_escalation_notice(command: str, failures: int) -> str:
    return f"[ESCALATION] {command} has failed {failures} time(s) consecutively."
