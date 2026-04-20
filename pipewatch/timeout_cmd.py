"""CLI subcommands for inspecting and testing timeout policies."""

from __future__ import annotations

import argparse
import json
from typing import List

from pipewatch.timeout_policy import (
    TimeoutPolicy,
    classify_duration,
    parse_policy,
    policy_to_dict,
)


def cmd_timeout_show(policy: TimeoutPolicy) -> None:
    """Print the current timeout policy as JSON."""
    print(json.dumps(policy_to_dict(policy), indent=2))


def cmd_timeout_check(args: argparse.Namespace, policy: TimeoutPolicy) -> int:
    """Check how a given elapsed duration would be classified."""
    elapsed = float(args.elapsed)
    command = args.command or ""
    result = classify_duration(elapsed, command, policy)
    timeout = policy.resolve_timeout(command)
    warn = policy.warn_threshold(command)
    print(f"Command : {command or '(any)'}")
    print(f"Elapsed : {elapsed:.1f}s")
    print(f"Timeout : {timeout if timeout is not None else 'none'}")
    print(f"Warn at : {warn:.1f}s" if warn is not None else "Warn at : n/a")
    print(f"Status  : {result}")
    return 0 if result != "exceeded" else 1


def add_timeout_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("timeout", help="Inspect timeout policies")
    sp = p.add_subparsers(dest="timeout_cmd")

    sp.add_parser("show", help="Print active timeout policy")

    chk = sp.add_parser("check", help="Classify an elapsed duration")
    chk.add_argument("elapsed", type=float, help="Elapsed seconds")
    chk.add_argument("--command", default="", help="Command string to match overrides")


def dispatch(args: argparse.Namespace, policy: TimeoutPolicy) -> int:
    if args.timeout_cmd == "show":
        cmd_timeout_show(policy)
        return 0
    if args.timeout_cmd == "check":
        return cmd_timeout_check(args, policy)
    print("No timeout subcommand given. Use 'show' or 'check'.")
    return 1
