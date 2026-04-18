"""CLI subcommands for label-based history queries."""
from __future__ import annotations
import argparse
from pipewatch.labeled_history import load_labeled_history, summarize_by_label
from pipewatch.label import parse_selector, filter_by_labels


def cmd_label_summary(args: argparse.Namespace) -> int:
    entries = load_labeled_history(args.history, [])
    selector = parse_selector(args.selector) if args.selector else {}
    filtered = filter_by_labels(entries, selector)
    if not filtered:
        print("No entries match.")
        return 0
    summary = summarize_by_label(filtered, args.group_by)
    print(f"{'Label':<20} {'Total':>6} {'Passed':>7} {'Avg Dur':>10}")
    print("-" * 46)
    for label_val, stats in sorted(summary.items()):
        print(f"{label_val:<20} {stats['total']:>6} {stats['passed']:>7} {stats['avg_duration']:>10.2f}s")
    return 0


def add_label_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("label-summary", help="Summarize history grouped by label")
    p.add_argument("--history", default=".pipewatch_history.json")
    p.add_argument("--selector", default="", help="Filter selector, e.g. env=prod,team=data")
    p.add_argument("--group-by", default="env", help="Label key to group by")
    p.set_defaults(func=cmd_label_summary)
