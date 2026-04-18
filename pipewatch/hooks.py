"""Post-run hooks: record history and optionally print a report."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pipewatch.history import DEFAULT_HISTORY_FILE, append_entry, load_history, make_entry
from pipewatch.report import summarize
from pipewatch.watcher import WatchResult
from pipewatch.format import truncate_stderr


def record(result: WatchResult, command: str, history_path: Path = DEFAULT_HISTORY_FILE) -> None:
    """Persist a WatchResult to history."""
    run = result.run_result
    entry = make_entry(
        command=command,
        exit_code=run.exit_code if run.exit_code is not None else -1,
        timed_out=run.timed_out,
        duration=run.duration,
        stderr_tail=truncate_stderr(run.stderr, max_chars=300),
    )
    append_entry(entry, path=history_path)


def print_report(history_path: Path = DEFAULT_HISTORY_FILE, last_n: int = 20) -> None:
    """Print a summary report to stdout."""
    entries = load_history(history_path)
    print(summarize(entries, last_n=last_n))


def run_hooks(
    result: WatchResult,
    command: str,
    history_path: Path = DEFAULT_HISTORY_FILE,
    show_report: bool = False,
    last_n: int = 20,
) -> None:
    """Run all post-job hooks."""
    record(result, command, history_path=history_path)
    if show_report:
        print_report(history_path=history_path, last_n=last_n)
