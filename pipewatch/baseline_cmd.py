"""CLI helpers for the baseline sub-command."""

from __future__ import annotations

import argparse
import sys
from typing import List

from pipewatch.baseline import check_baseline, compute_baseline, format_baseline
from pipewatch.history import load_history


def cmd_baseline(args: argparse.Namespace) -> int:
    """Print baseline analysis for a command against its history."""
    entries = load_history(args.history_file)
    if not entries:
        print("No history found.", file=sys.stderr)
        return 1

    multiplier: float = args.multiplier
    command: str = args.command

    stats = compute_baseline(entries, command, multiplier=multiplier)
    if stats is None:
        print(f"No successful history entries for command: {command}", file=sys.stderr)
        return 1

    # Use the most recent run's duration for the check
    recent = next(
        (e for e in reversed(entries) if e.command == command),
        None,
    )
    if recent is None:
        print("No recent entry found.", file=sys.stderr)
        return 1

    result = check_baseline(stats, recent.duration)
    print(format_baseline(result))
    return 1 if result.exceeded else 0


def add_baseline_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p: argparse.ArgumentParser = subparsers.add_parser(
        "baseline",
        help="Check whether the latest run exceeded its historical baseline.",
    )
    p.add_argument("command", help="Command string to look up in history.")
    p.add_argument(
        "--history-file",
        default=".pipewatch_history.jsonl",
        help="Path to history file.",
    )
    p.add_argument(
        "--multiplier",
        type=float,
        default=2.0,
        help="Threshold = avg_duration * multiplier (default: 2.0).",
    )
    p.set_defaults(func=cmd_baseline)
