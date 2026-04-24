"""Runtime budget tracking: flag commands that exceed expected duration budgets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BudgetRule:
    command: str
    max_seconds: float
    warn_seconds: Optional[float] = None  # warn before hard limit


@dataclass
class BudgetResult:
    command: str
    duration: float
    max_seconds: float
    warn_seconds: Optional[float]
    exceeded: bool
    warned: bool
    overage: float  # seconds over budget (0 if within)


def parse_budget_rules(raw: List[Dict]) -> List[BudgetRule]:
    """Parse a list of dicts into BudgetRule objects."""
    rules = []
    for item in raw:
        rules.append(
            BudgetRule(
                command=item["command"],
                max_seconds=float(item["max_seconds"]),
                warn_seconds=float(item["warn_seconds"]) if "warn_seconds" in item else None,
            )
        )
    return rules


def find_rule(rules: List[BudgetRule], command: str) -> Optional[BudgetRule]:
    """Return the first rule whose command string matches exactly."""
    for rule in rules:
        if rule.command == command:
            return rule
    return None


def check_budget(rule: BudgetRule, duration: float) -> BudgetResult:
    """Evaluate a single run against its budget rule."""
    exceeded = duration > rule.max_seconds
    warned = (
        not exceeded
        and rule.warn_seconds is not None
        and duration > rule.warn_seconds
    )
    overage = max(0.0, duration - rule.max_seconds)
    return BudgetResult(
        command=rule.command,
        duration=duration,
        max_seconds=rule.max_seconds,
        warn_seconds=rule.warn_seconds,
        exceeded=exceeded,
        warned=warned,
        overage=overage,
    )


def format_budget_result(result: BudgetResult) -> str:
    """Return a human-readable summary line for a budget check."""
    if result.exceeded:
        return (
            f"BUDGET EXCEEDED [{result.command}]: "
            f"{result.duration:.1f}s > {result.max_seconds:.1f}s "
            f"(+{result.overage:.1f}s over)"
        )
    if result.warned:
        return (
            f"BUDGET WARNING [{result.command}]: "
            f"{result.duration:.1f}s approaching limit of {result.max_seconds:.1f}s"
        )
    return (
        f"BUDGET OK [{result.command}]: "
        f"{result.duration:.1f}s within {result.max_seconds:.1f}s"
    )
