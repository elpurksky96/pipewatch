"""Output pattern matching — alert when command output matches/doesn't match a pattern."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional
from pipewatch.runner import RunResult


@dataclass
class PatternRule:
    pattern: str
    match_on: str = "stdout"  # stdout | stderr
    invert: bool = False      # True => alert when NOT matched
    label: str = ""

    def compiled(self) -> re.Pattern:
        return re.compile(self.pattern, re.MULTILINE)


@dataclass
class PatternResult:
    rule: PatternRule
    matched: bool
    triggered: bool  # matched XOR invert
    excerpt: str = ""


def check_pattern(result: RunResult, rule: PatternRule) -> PatternResult:
    text = result.stdout if rule.match_on == "stdout" else result.stderr
    rx = rule.compiled()
    m = rx.search(text or "")
    matched = m is not None
    triggered = matched if not rule.invert else not matched
    excerpt = ""
    if m:
        start = max(0, m.start() - 20)
        excerpt = text[start: m.end() + 40].strip()
    return PatternResult(rule=rule, matched=matched, triggered=triggered, excerpt=excerpt)


def check_all_patterns(result: RunResult, rules: list[PatternRule]) -> list[PatternResult]:
    return [check_pattern(result, r) for r in rules]


def any_triggered(results: list[PatternResult]) -> bool:
    return any(r.triggered for r in results)


def format_pattern_results(results: list[PatternResult]) -> str:
    lines = []
    for pr in results:
        status = "TRIGGERED" if pr.triggered else "ok"
        label = f" [{pr.rule.label}]" if pr.rule.label else ""
        lines.append(f"  {status}{label}: /{pr.rule.pattern}/ on {pr.rule.match_on}")
        if pr.triggered and pr.excerpt:
            lines.append(f"    excerpt: {pr.excerpt!r}")
    return "\n".join(lines)
