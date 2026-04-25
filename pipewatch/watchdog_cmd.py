"""CLI sub-commands for the watchdog feature."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipewatch.watchdog import parse_watchdog_rules, check_watchdog, format_watchdog_result
from pipewatch.watchdog_state import get_last_seen, record_seen, clear_seen, all_seen


def _load_rules(rules_path: str) -> list:
    p = Path(rules_path)
    if not p.exists():
        return []
    return json.loads(p.read_text())


def cmd_watchdog_check(args: argparse.Namespace) -> int:
    raw = _load_rules(args.rules)
    if not raw:
        print("No watchdog rules found.")
        return 0

    rules = parse_watchdog_rules(raw)
    state_path = Path(args.state)
    triggered_any = False

    for rule in rules:
        last = get_last_seen(rule.command, path=state_path)
        result = check_watchdog(rule, last)
        print(format_watchdog_result(result))
        if result.triggered:
            triggered_any = True

    return 1 if triggered_any else 0


def cmd_watchdog_ping(args: argparse.Namespace) -> int:
    state_path = Path(args.state)
    ts = record_seen(args.command, path=state_path)
    print(f"Recorded last-seen for '{args.command}' at {ts}")
    return 0


def cmd_watchdog_status(args: argparse.Namespace) -> int:
    entries = all_seen(path=Path(args.state))
    if not entries:
        print("No watchdog entries recorded.")
        return 0
    for cmd, ts in sorted(entries.items()):
        print(f"  {cmd}: {ts}")
    return 0


def add_watchdog_subparser(sub: argparse._SubParsersAction) -> None:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--state", default=".pipewatch/watchdog_state.json")

    p_check = sub.add_parser("watchdog-check", parents=[common], help="Check watchdog rules")
    p_check.add_argument("--rules", default=".pipewatch/watchdog_rules.json")
    p_check.set_defaults(func=cmd_watchdog_check)

    p_ping = sub.add_parser("watchdog-ping", parents=[common], help="Record a heartbeat for a command")
    p_ping.add_argument("command", help="Command identifier to ping")
    p_ping.set_defaults(func=cmd_watchdog_ping)

    p_status = sub.add_parser("watchdog-status", parents=[common], help="Show all last-seen entries")
    p_status.set_defaults(func=cmd_watchdog_status)


def dispatch(args: argparse.Namespace) -> int:
    return args.func(args)
