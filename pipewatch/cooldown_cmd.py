"""CLI subcommands for managing alert cooldowns."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.cooldown import DEFAULT_PATH, describe, is_in_cooldown, reset


def cmd_cooldown_status(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "state_path", DEFAULT_PATH))
    print(describe(path=path))
    return 0


def cmd_cooldown_reset(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "state_path", DEFAULT_PATH))
    key = getattr(args, "key", None)
    reset(key=key, path=path)
    if key:
        print(f"Cooldown reset for: {key}")
    else:
        print("All cooldown entries reset.")
    return 0


def cmd_cooldown_check(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "state_path", DEFAULT_PATH))
    window = getattr(args, "window", 300)
    key = args.key
    if is_in_cooldown(key, window_seconds=window, path=path):
        print(f"{key}: IN cooldown (window={window}s)")
        return 1
    print(f"{key}: not in cooldown")
    return 0


def add_cooldown_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("cooldown", help="Manage alert cooldowns")
    sub = p.add_subparsers(dest="cooldown_cmd")

    sub.add_parser("status", help="Show current cooldown state")

    p_reset = sub.add_parser("reset", help="Reset cooldown entries")
    p_reset.add_argument("key", nargs="?", default=None, help="Key to reset (omit for all)")

    p_check = sub.add_parser("check", help="Check if a key is in cooldown")
    p_check.add_argument("key", help="Cooldown key to check")
    p_check.add_argument("--window", type=int, default=300, help="Cooldown window in seconds")


def dispatch(args: argparse.Namespace) -> int:
    cmd = getattr(args, "cooldown_cmd", None)
    if cmd == "status" or cmd is None:
        return cmd_cooldown_status(args)
    if cmd == "reset":
        return cmd_cooldown_reset(args)
    if cmd == "check":
        return cmd_cooldown_check(args)
    print(f"Unknown cooldown subcommand: {cmd}")
    return 1
