"""CLI helpers for inspecting and resetting alert throttle state."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Optional

from pipewatch.throttle import _load_state, _save_state, DEFAULT_COOLDOWN

DEFAULT_STATE = Path(".pipewatch") / "throttle.json"


def cmd_throttle_status(args: argparse.Namespace) -> int:
    path = Path(args.state) if args.state else DEFAULT_STATE
    state = _load_state(path)
    if not state.last_alert:
        print("No throttle records found.")
        return 0
    now = time.time()
    cooldown = args.cooldown
    print(f"{'Key':<40} {'Last alert':<26} Status")
    print("-" * 75)
    for key, ts in sorted(state.last_alert.items()):
        age = now - ts
        status = "throttled" if age < cooldown else "ready"
        human = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        print(f"{key:<40} {human:<26} {status}")
    return 0


def cmd_throttle_reset(args: argparse.Namespace) -> int:
    path = Path(args.state) if args.state else DEFAULT_STATE
    state = _load_state(path)
    key: Optional[str] = args.key
    if key:
        removed = state.last_alert.pop(key, None)
        if removed is None:
            print(f"Key '{key}' not found in throttle state.")
            return 1
        _save_state(state, path)
        print(f"Reset throttle for '{key}'.")
    else:
        state.last_alert.clear()
        _save_state(state, path)
        print("Throttle state cleared.")
    return 0


def add_throttle_subparser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("throttle", help="Inspect or reset alert throttle state")
    sp = p.add_subparsers(dest="throttle_cmd")

    status_p = sp.add_parser("status", help="Show current throttle state")
    status_p.add_argument("--cooldown", type=int, default=DEFAULT_COOLDOWN)
    status_p.add_argument("--state", default=None)
    status_p.set_defaults(func=cmd_throttle_status)

    reset_p = sp.add_parser("reset", help="Reset throttle for a key or all keys")
    reset_p.add_argument("key", nargs="?", default=None)
    reset_p.add_argument("--state", default=None)
    reset_p.set_defaults(func=cmd_throttle_reset)
