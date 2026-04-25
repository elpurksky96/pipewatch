"""SLA (Service Level Agreement) tracking for pipeline jobs.

Defines success-rate and max-duration thresholds per command and
checks recent history against those thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SLARule:
    command: str
    min_success_rate: Optional[float] = None   # 0.0 – 1.0
    max_duration_seconds: Optional[float] = None
    window: int = 20  # number of most-recent entries to consider


@dataclass
class SLAResult:
    command: str
    passed: bool
    success_rate: Optional[float]
    avg_duration: Optional[float]
    violations: List[str] = field(default_factory=list)


def parse_sla_rules(raw: List[Dict]) -> List[SLARule]:
    """Build SLARule objects from a list of plain dicts (e.g. from JSON/YAML)."""
    rules = []
    for item in raw:
        rules.append(
            SLARule(
                command=item["command"],
                min_success_rate=item.get("min_success_rate"),
                max_duration_seconds=item.get("max_duration_seconds"),
                window=int(item.get("window", 20)),
            )
        )
    return rules


def find_rule(rules: List[SLARule], command: str) -> Optional[SLARule]:
    for rule in rules:
        if rule.command == command:
            return rule
    return None


def check_sla(rule: SLARule, entries: list) -> SLAResult:
    """Evaluate *entries* (most-recent first or last) against *rule*.

    Each entry must expose ``.success`` (bool) and ``.duration`` (float).
    """
    recent = entries[-rule.window:] if len(entries) > rule.window else entries

    if not recent:
        return SLAResult(
            command=rule.command,
            passed=True,
            success_rate=None,
            avg_duration=None,
        )

    successes = [e for e in recent if e.success]
    rate = len(successes) / len(recent)
    durations = [e.duration for e in recent if e.duration is not None]
    avg_dur = sum(durations) / len(durations) if durations else None

    violations: List[str] = []

    if rule.min_success_rate is not None and rate < rule.min_success_rate:
        violations.append(
            f"success rate {rate:.0%} below minimum {rule.min_success_rate:.0%}"
        )

    if rule.max_duration_seconds is not None and avg_dur is not None:
        if avg_dur > rule.max_duration_seconds:
            violations.append(
                f"avg duration {avg_dur:.1f}s exceeds max {rule.max_duration_seconds:.1f}s"
            )

    return SLAResult(
        command=rule.command,
        passed=len(violations) == 0,
        success_rate=rate,
        avg_duration=avg_dur,
        violations=violations,
    )


def format_sla_result(result: SLAResult) -> str:
    status = "OK" if result.passed else "BREACH"
    rate_str = f"{result.success_rate:.0%}" if result.success_rate is not None else "n/a"
    dur_str = f"{result.avg_duration:.1f}s" if result.avg_duration is not None else "n/a"
    base = f"[{status}] {result.command}  success={rate_str}  avg_dur={dur_str}"
    if result.violations:
        base += "\n  " + "\n  ".join(result.violations)
    return base
