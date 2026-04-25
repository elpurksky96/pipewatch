"""CLI subcommand for replaying / inspecting historical runs."""

from __future__ import annotations

import argparse
import sys
from typing import List

from pipewatch.replay import format_replay_summary, load_entries_for_command, replay


def cmd_replay_list(args: argparse.Namespace) -> int:
    """List historical entries for a command."""
    entries = load_entries_for_command(
        args.command,
        history_path=args.history,
        limit=args.limit,
    )
    if not entries:
        print(f"No history found for: {args.command}")
        return 0
    for e in entries:
        status = "OK" if e.success else "FAIL"
        print(f"  [{status}] {e.timestamp}  duration={e.duration:.2f}s")
    return 0


def cmd_replay_dry_run(args: argparse.Namespace) -> int:
    """Dry-run replay: show what would be replayed."""
    result = replay(
        args.command,
        history_path=args.history,
        limit=args.limit,
        only_failures=args.only_failures,
    )
    print(format_replay_summary(result))
    return 0


def add_replay_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("replay", help="Inspect or replay historical runs")
    parser.add_argument("--history", default=".pipewatch_history.json", metavar="FILE")
    sub = parser.add_subparsers(dest="replay_cmd")

    p_list = sub.add_parser("list", help="List past runs for a command")
    p_list.add_argument("command", help="Pipeline command to look up")
    p_list.add_argument("--limit", type=int, default=None, metavar="N")
    p_list.set_defaults(func=cmd_replay_list)

    p_dry = sub.add_parser("dry-run", help="Show what would be replayed")
    p_dry.add_argument("command", help="Pipeline command to look up")
    p_dry.add_argument("--limit", type=int, default=None, metavar="N")
    p_dry.add_argument(
        "--only-failures", action="store_true", dest="only_failures",
        help="Only include failed runs",
    )
    p_dry.set_defaults(func=cmd_replay_dry_run)


def dispatch(args: argparse.Namespace) -> int:
    if not getattr(args, "replay_cmd", None):
        print("Usage: pipewatch replay {list,dry-run}", file=sys.stderr)
        return 1
    return args.func(args)  # type: ignore[no-any-return]
