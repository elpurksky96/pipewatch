"""CLI subcommands for runtime budget management."""

from __future__ import annotations

import argparse
import json
from typing import List

from pipewatch.budget import (
    BudgetRule,
    check_budget,
    find_rule,
    format_budget_result,
    parse_budget_rules,
)
from pipewatch.history import load_history


def _load_rules(path: str) -> List[BudgetRule]:
    try:
        with open(path) as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        return []
    return parse_budget_rules(raw if isinstance(raw, list) else [])


def cmd_budget_check(args: argparse.Namespace) -> int:
    """Check the most-recent run of a command against its budget."""
    rules = _load_rules(args.budget_file)
    rule = find_rule(rules, args.command)
    if rule is None:
        print(f"No budget rule found for command: {args.command}")
        return 1

    history = load_history(args.history_file)
    runs = [e for e in history if e.command == args.command]
    if not runs:
        print(f"No history found for command: {args.command}")
        return 1

    latest = runs[-1]
    result = check_budget(rule, latest.duration)
    print(format_budget_result(result))
    return 1 if result.exceeded else 0


def cmd_budget_list(args: argparse.Namespace) -> int:
    """List all configured budget rules."""
    rules = _load_rules(args.budget_file)
    if not rules:
        print("No budget rules configured.")
        return 0
    for rule in rules:
        warn_part = f", warn at {rule.warn_seconds}s" if rule.warn_seconds is not None else ""
        print(f"  {rule.command}: max {rule.max_seconds}s{warn_part}")
    return 0


def add_budget_subparser(sub: argparse._SubParsersAction) -> None:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--budget-file", default=".pipewatch_budgets.json")
    common.add_argument("--history-file", default=".pipewatch_history.json")

    p_budget = sub.add_parser("budget", help="Runtime budget commands")
    budget_sub = p_budget.add_subparsers(dest="budget_cmd")

    p_check = budget_sub.add_parser("check", parents=[common], help="Check latest run vs budget")
    p_check.add_argument("command", help="Command string to check")
    p_check.set_defaults(func=cmd_budget_check)

    p_list = budget_sub.add_parser("list", parents=[common], help="List budget rules")
    p_list.set_defaults(func=cmd_budget_list)


def dispatch(args: argparse.Namespace) -> int:
    if hasattr(args, "func"):
        return args.func(args)
    print("Usage: pipewatch budget {check,list}")
    return 1
