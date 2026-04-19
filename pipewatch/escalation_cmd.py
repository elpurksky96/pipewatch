"""CLI subcommands for escalation state management."""
from __future__ import annotations
import argparse
from pathlib import Path

from pipewatch.escalation import (
    DEFAULT_STATE_PATH,
    _load_all,
    _save_all,
    load_state,
)


def cmd_escalation_status(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "state_path", DEFAULT_STATE_PATH))
    data = _load_all(path)
    if not data:
        print("No escalation state recorded.")
        return 0
    for key, entry in data.items():
        failures = entry.get("consecutive_failures", 0)
        escalated = entry.get("escalated", False)
        flag = " [ESCALATED]" if escalated else ""
        print(f"{key}: {failures} consecutive failure(s){flag}")
    return 0


def cmd_escalation_reset(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "state_path", DEFAULT_STATE_PATH))
    key = getattr(args, "key", None)
    data = _load_all(path)
    if key:
        if key not in data:
            print(f"No escalation state for key: {key}")
            return 1
        del data[key]
        print(f"Reset escalation state for: {key}")
    else:
        data = {}
        print("Reset all escalation state.")
    _save_all(data, path)
    return 0


def add_escalation_subparser(subparsers) -> None:
    p = subparsers.add_parser("escalation", help="Manage alert escalation state")
    sub = p.add_subparsers(dest="escalation_cmd")

    sub.add_parser("status", help="Show current escalation state")

    reset_p = sub.add_parser("reset", help="Reset escalation state")
    reset_p.add_argument("key", nargs="?", help="Command key to reset (omit for all)")

    def _dispatch(args):
        if args.escalation_cmd == "status":
            return cmd_escalation_status(args)
        if args.escalation_cmd == "reset":
            return cmd_escalation_reset(args)
        p.print_help()
        return 1

    p.set_defaults(func=_dispatch)
