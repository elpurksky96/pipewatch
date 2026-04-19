"""CLI subcommands for inspecting captured output."""
from __future__ import annotations

import argparse
from typing import List

from pipewatch.output_capture import load_outputs, filter_by_command, CapturedOutput


def _print_entry(entry: CapturedOutput, verbose: bool = False) -> None:
    status = "TIMEOUT" if entry.timed_out else ("OK" if entry.exit_code == 0 else "FAIL")
    tags = ",".join(entry.tags) if entry.tags else "-"
    print(f"[{entry.timestamp}] {entry.command!r:40s} {status:7s} exit={entry.exit_code} tags={tags}")
    if verbose:
        if entry.stdout.strip():
            print("  stdout:", entry.stdout[:200].replace("\n", "\n          "))
        if entry.stderr.strip():
            print("  stderr:", entry.stderr[:200].replace("\n", "\n          "))


def cmd_output_list(args: argparse.Namespace) -> int:
    entries = load_outputs(args.file)
    if args.command:
        entries = filter_by_command(entries, args.command)
    if not entries:
        print("No captured output found.")
        return 0
    for entry in entries[-args.tail:]:
        _print_entry(entry, verbose=args.verbose)
    return 0


def cmd_output_show(args: argparse.Namespace) -> int:
    entries = load_outputs(args.file)
    if args.command:
        entries = filter_by_command(entries, args.command)
    if not entries:
        print("No entries found.")
        return 1
    entry = entries[-1]
    print(f"Command  : {entry.command}")
    print(f"Timestamp: {entry.timestamp}")
    print(f"Exit code: {entry.exit_code}")
    print(f"Timed out: {entry.timed_out}")
    print(f"Tags     : {', '.join(entry.tags) or '-'}")
    print("--- stdout ---")
    print(entry.stdout or "(empty)")
    print("--- stderr ---")
    print(entry.stderr or "(empty)")
    return 0


def add_output_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("output", help="Inspect captured command output")
    sp = p.add_subparsers(dest="output_cmd")

    ls = sp.add_parser("list", help="List captured output entries")
    ls.add_argument("--command", default=None, help="Filter by command string")
    ls.add_argument("--tail", type=int, default=20, help="Show last N entries")
    ls.add_argument("--verbose", action="store_true", help="Show stdout/stderr preview")
    ls.add_argument("--file", default=".pipewatch_output.jsonl")

    sh = sp.add_parser("show", help="Show full output of last matching entry")
    sh.add_argument("--command", default=None)
    sh.add_argument("--file", default=".pipewatch_output.jsonl")


def dispatch(args: argparse.Namespace) -> int:
    if args.output_cmd == "list":
        return cmd_output_list(args)
    if args.output_cmd == "show":
        return cmd_output_show(args)
    print("Usage: pipewatch output {list,show}")
    return 1
