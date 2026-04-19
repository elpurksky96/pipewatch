"""CLI helpers for pattern-match rules."""
from __future__ import annotations
import argparse
from pipewatch.pattern import PatternRule, check_all_patterns, format_pattern_results, any_triggered
from pipewatch.runner import run_command


def _parse_rules(args: argparse.Namespace) -> list[PatternRule]:
    rules: list[PatternRule] = []
    for spec in getattr(args, "match", []) or []:
        rules.append(PatternRule(pattern=spec, match_on="stdout"))
    for spec in getattr(args, "match_stderr", []) or []:
        rules.append(PatternRule(pattern=spec, match_on="stderr"))
    for spec in getattr(args, "no_match", []) or []:
        rules.append(PatternRule(pattern=spec, match_on="stdout", invert=True))
    return rules


def cmd_pattern_check(args: argparse.Namespace) -> int:
    rules = _parse_rules(args)
    if not rules:
        print("No pattern rules specified.")
        return 1

    timeout = getattr(args, "timeout", 60)
    result = run_command(args.command, timeout=timeout)
    pattern_results = check_all_patterns(result, rules)

    print(format_pattern_results(pattern_results))

    if any_triggered(pattern_results):
        print("[pipewatch] One or more pattern rules triggered.")
        return 2
    print("[pipewatch] All pattern rules passed.")
    return 0


def add_pattern_subparser(subparsers) -> None:
    p: argparse.ArgumentParser = subparsers.add_parser(
        "pattern", help="Run a command and check its output against patterns."
    )
    p.add_argument("command", help="Command to run")
    p.add_argument(
        "--match", metavar="REGEX", action="append",
        help="Trigger alert if stdout matches REGEX",
    )
    p.add_argument(
        "--match-stderr", metavar="REGEX", action="append",
        help="Trigger alert if stderr matches REGEX",
    )
    p.add_argument(
        "--no-match", metavar="REGEX", action="append",
        help="Trigger alert if stdout does NOT match REGEX",
    )
    p.add_argument("--timeout", type=float, default=60, help="Timeout in seconds")
    p.set_defaults(func=cmd_pattern_check)
