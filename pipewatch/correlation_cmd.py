"""CLI subcommand: pipewatch correlation."""

from __future__ import annotations

import argparse

from pipewatch.correlation import (
    find_correlated_failures,
    format_correlation_report,
)
from pipewatch.history import load_history


def cmd_correlation(
    args: argparse.Namespace,
    history_path: str = "pipewatch_history.jsonl",
) -> int:
    entries = load_history(history_path)
    if not entries:
        print("No history entries found.")
        return 0

    field_name: str = args.field
    min_rate: float = args.min_failure_rate
    min_samples: int = args.min_samples

    groups = find_correlated_failures(
        entries,
        field_name=field_name,
        min_failure_rate=min_rate,
        min_samples=min_samples,
    )
    report = format_correlation_report(groups, field_name)
    print(report)
    return 0 if groups else 0


def add_correlation_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "correlation",
        help="Find correlated failure patterns in run history.",
    )
    p.add_argument(
        "--field",
        default="command",
        help="Entry field to group by (default: command).",
    )
    p.add_argument(
        "--min-failure-rate",
        type=float,
        default=0.5,
        dest="min_failure_rate",
        help="Minimum failure rate to report (default: 0.5).",
    )
    p.add_argument(
        "--min-samples",
        type=int,
        default=2,
        dest="min_samples",
        help="Minimum number of samples required (default: 2).",
    )
    p.set_defaults(func=cmd_correlation)
