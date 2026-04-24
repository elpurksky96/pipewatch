"""CLI subcommands for quota management."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipewatch.quota import (
    QuotaRule,
    current_count,
    is_quota_exceeded,
    parse_quota_rules,
    find_rule,
    record_run,
    _load,
    _save,
)

DEFAULT_STATE = Path(".pipewatch/quota_state.json")
DEFAULT_RULES = Path(".pipewatch/quota_rules.json")


def _load_rules(rules_path: Path) -> list:
    if not rules_path.exists():
        return []
    try:
        return parse_quota_rules(json.loads(rules_path.read_text()))
    except (json.JSONDecodeError, KeyError, OSError):
        return []


def cmd_quota_status(args: argparse.Namespace) -> int:
    rules_path = Path(getattr(args, "rules", DEFAULT_RULES))
    state_path = Path(getattr(args, "state", DEFAULT_STATE))
    rules = _load_rules(rules_path)
    if not rules:
        print("No quota rules configured.")
        return 0
    for rule in rules:
        count = current_count(rule, state_path)
        exceeded = is_quota_exceeded(rule, state_path)
        status = "EXCEEDED" if exceeded else "ok"
        print(
            f"{rule.command}: {count}/{rule.max_runs} runs "
            f"in {rule.window_seconds}s window [{status}]"
        )
    return 0


def cmd_quota_check(args: argparse.Namespace) -> int:
    rules_path = Path(getattr(args, "rules", DEFAULT_RULES))
    state_path = Path(getattr(args, "state", DEFAULT_STATE))
    command = args.command
    rules = _load_rules(rules_path)
    rule = find_rule(rules, command)
    if rule is None:
        print(f"No quota rule for: {command}")
        return 0
    if is_quota_exceeded(rule, state_path):
        print(f"QUOTA EXCEEDED: {command} ({rule.max_runs} runs / {rule.window_seconds}s)")
        return 1
    count = current_count(rule, state_path)
    print(f"OK: {command} {count}/{rule.max_runs} runs used")
    return 0


def cmd_quota_reset(args: argparse.Namespace) -> int:
    state_path = Path(getattr(args, "state", DEFAULT_STATE))
    command = getattr(args, "command", None)
    data = _load(state_path)
    if command:
        data.pop(command, None)
        print(f"Reset quota state for: {command}")
    else:
        data = {}
        print("Reset all quota state.")
    _save(state_path, data)
    return 0


def add_quota_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("quota", help="Manage run quotas")
    sub = p.add_subparsers(dest="quota_cmd")

    sub.add_parser("status", help="Show quota usage for all rules")

    chk = sub.add_parser("check", help="Check quota for a specific command")
    chk.add_argument("command")

    rst = sub.add_parser("reset", help="Reset quota state")
    rst.add_argument("command", nargs="?", default=None)


def dispatch(args: argparse.Namespace) -> int:
    cmd = getattr(args, "quota_cmd", None)
    if cmd == "status":
        return cmd_quota_status(args)
    if cmd == "check":
        return cmd_quota_check(args)
    if cmd == "reset":
        return cmd_quota_reset(args)
    print("Usage: pipewatch quota {status,check,reset}")
    return 1
