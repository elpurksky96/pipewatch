"""Stale job detection: flag commands that haven't run recently."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class StalenessRule:
    command: str
    max_gap_hours: float


@dataclass
class StalenessResult:
    command: str
    max_gap_hours: float
    last_run_iso: Optional[str]
    hours_since: Optional[float]
    is_stale: bool


def _parse_rules(raw: List[dict]) -> List[StalenessRule]:
    rules = []
    for item in raw:
        rules.append(
            StalenessRule(
                command=item["command"],
                max_gap_hours=float(item["max_gap_hours"]),
            )
        )
    return rules


def _hours_since(iso: str, now: datetime) -> float:
    ts = datetime.fromisoformat(iso)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    delta = now - ts
    return delta.total_seconds() / 3600.0


def check_staleness(
    rule: StalenessRule,
    history: list,
    now: Optional[datetime] = None,
) -> StalenessResult:
    """Return a StalenessResult for *rule* given a list of history entries."""
    if now is None:
        now = datetime.now(timezone.utc)

    matching = [
        e for e in history if getattr(e, "command", None) == rule.command
    ]

    if not matching:
        return StalenessResult(
            command=rule.command,
            max_gap_hours=rule.max_gap_hours,
            last_run_iso=None,
            hours_since=None,
            is_stale=True,
        )

    last_iso = max(getattr(e, "timestamp", "") for e in matching)
    hours = _hours_since(last_iso, now)
    return StalenessResult(
        command=rule.command,
        max_gap_hours=rule.max_gap_hours,
        last_run_iso=last_iso,
        hours_since=round(hours, 2),
        is_stale=hours > rule.max_gap_hours,
    )


def format_staleness(result: StalenessResult) -> str:
    status = "STALE" if result.is_stale else "OK"
    if result.last_run_iso is None:
        detail = "never run"
    else:
        detail = f"last run {result.hours_since:.1f}h ago (limit {result.max_gap_hours}h)"
    return f"[{status}] {result.command}: {detail}"
