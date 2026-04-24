"""Budget integration hooks: check budget after each run and emit warnings."""

from __future__ import annotations

from typing import List, Optional

from pipewatch.budget import (
    BudgetRule,
    BudgetResult,
    check_budget,
    find_rule,
    format_budget_result,
)
from pipewatch.runner import RunResult


def evaluate_budget(
    result: RunResult,
    command: str,
    rules: List[BudgetRule],
) -> Optional[BudgetResult]:
    """Return a BudgetResult if a rule exists for the command, else None."""
    rule = find_rule(rules, command)
    if rule is None:
        return None
    return check_budget(rule, result.duration)


def print_budget_notice(budget_result: BudgetResult) -> None:
    """Print a budget notice to stdout if the run warned or exceeded."""
    if budget_result.exceeded or budget_result.warned:
        print(format_budget_result(budget_result))


def budget_hook(result: RunResult, command: str, rules: List[BudgetRule]) -> Optional[BudgetResult]:
    """Convenience hook: evaluate and print budget notice in one call.

    Returns the BudgetResult if a rule matched, otherwise None.
    """
    budget_result = evaluate_budget(result, command, rules)
    if budget_result is not None:
        print_budget_notice(budget_result)
    return budget_result


def any_budget_exceeded(results: List[BudgetResult]) -> bool:
    """Return True if any BudgetResult in the list exceeded its limit."""
    return any(r.exceeded for r in results)


def summarize_budget_results(results: List[BudgetResult]) -> str:
    """Return a multi-line summary of all budget results."""
    if not results:
        return "No budget rules matched."
    lines = [format_budget_result(r) for r in results]
    return "\n".join(lines)
