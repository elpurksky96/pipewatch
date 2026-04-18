"""Send Slack alerts for pipeline run results."""

import json
import urllib.request
import urllib.error
from typing import Optional

from pipewatch.runner import RunResult


def _build_payload(result: RunResult, job_name: str) -> dict:
    if result.timed_out:
        status = ":alarm_clock: *TIMED OUT*"
    elif result.success:
        status = ":white_check_mark: *SUCCESS*"
    else:
        status = ":x: *FAILED*"

    lines = [
        f"{status} — `{job_name}`",
        f"Command: `{result.command}`",
        f"Duration: {result.duration_seconds}s",
    ]
    if not result.success:
        snippet = (result.stderr or result.stdout or "").strip()[-500:]
        if snippet:
            lines.append(f"```{snippet}```")

    return {"text": "\n".join(lines)}


def send_slack_alert(
    webhook_url: str,
    result: RunResult,
    job_name: str = "pipeline",
    only_on_failure: bool = True,
) -> bool:
    """Post a Slack message. Returns True if sent successfully."""
    if only_on_failure and result.success:
        return False

    payload = _build_payload(result, job_name)
    data = json.dumps(payload).encode()

    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except urllib.error.URLError:
        return False
