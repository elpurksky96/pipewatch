"""CLI subcommand: anomaly — check recent run durations for anomalies."""

from __future__ import annotations

import argparse
import sys
from typing import List

from pipewatch.anomaly import detect_anomaly, format_anomaly
from pipewatch.history import load_history, HistoryEntry


def _durations_for_command(entries: List[HistoryEntry], command: str) -> List[float]:
    return [
        e.duration
        for e in entries
        if e.command == command and not e.timed_out
    ]


def cmd_anomaly_check(args: argparse.Namespace) -> int:
    entries = load_history(args.history_file)

    if not entries:
        print("No history entries found.", file=sys.stderr)
        return 1

    # Use the most recent entry as the subject
    recent = [
        e for e in entries
        if args.command is None or e.command == args.command
    ]

    if not recent:
        print(f"No entries found for command: {args.command}", file=sys.stderr)
        return 1

    subject = recent[-1]
    historical = _durations_for_command(entries[:-1], subject.command)

    result = detect_anomaly(
        command=subject.command,
        current_duration=subject.duration,
        historical_durations=historical,
        threshold=args.threshold,
        min_samples=args.min_samples,
    )

    if result is None:
        print(f"Not enough data to evaluate anomaly (need {args.min_samples} samples).")
        return 0

    print(format_anomaly(result))
    return 2 if result.is_anomaly else 0


def add_anomaly_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("anomaly", help="Detect anomalous run durations")
    p.add_argument("--command", default=None, help="Filter by command string")
    p.add_argument("--threshold", type=float, default=2.5, help="Z-score threshold (default: 2.5)")
    p.add_argument("--min-samples", type=int, default=5, dest="min_samples",
                   help="Minimum historical samples required (default: 5)")
    p.add_argument("--history-file", default=".pipewatch_history.json", dest="history_file")
    p.set_defaults(func=cmd_anomaly_check)
