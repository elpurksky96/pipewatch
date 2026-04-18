"""Daemon loop: run a command on a schedule and trigger hooks."""

from __future__ import annotations

import time
import logging
from datetime import datetime
from typing import Optional

from pipewatch.schedule import ScheduleConfig, is_due
from pipewatch.runner import run_command
from pipewatch.hooks import run_hooks
from pipewatch.config import PipewatchConfig

logger = logging.getLogger(__name__)

_DEFAULT_POLL_SECONDS = 60


def _wait_until_next_minute(poll: float = _DEFAULT_POLL_SECONDS) -> None:
    """Sleep until the next poll boundary."""
    time.sleep(poll)


def run_daemon(
    command: str,
    schedule: ScheduleConfig,
    config: PipewatchConfig,
    *,
    max_runs: Optional[int] = None,
    poll_seconds: float = _DEFAULT_POLL_SECONDS,
    _now_fn=None,  # injectable for testing
    _sleep_fn=None,
) -> int:
    """
    Poll on `poll_seconds` interval; when the schedule is due, run the command.
    Returns the number of runs executed.
    """
    if _now_fn is None:
        _now_fn = datetime.utcnow
    if _sleep_fn is None:
        _sleep_fn = lambda: time.sleep(poll_seconds)

    runs = 0
    last_run_minute: Optional[str] = None

    logger.info("pipewatch daemon started — %s", schedule)

    while True:
        now = _now_fn()
        minute_key = now.strftime("%Y-%m-%dT%H:%M")

        if minute_key != last_run_minute and is_due(schedule, now):
            last_run_minute = minute_key
            logger.info("Running command at %s", minute_key)
            result = run_command(command, timeout=config.timeout)
            run_hooks(result, config)
            runs += 1
            if max_runs is not None and runs >= max_runs:
                logger.info("Reached max_runs=%d, stopping.", max_runs)
                return runs

        _sleep_fn()
