"""Watchdog: detect commands that have stopped running within an expected cadence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class WatchdogRule:
    command: str
    max_silence_minutes: int
    tags: List[str] = field(default_factory=list)


@dataclass
class WatchdogResult:
    command: str
    last_seen: Optional[str]
    silence_minutes: Optional[float]
    threshold_minutes: int
    triggered: bool
    message: str


def parse_watchdog_rules(raw: list) -> List[WatchdogRule]:
    rules = []
    for item in raw:
        rules.append(WatchdogRule(
            command=item["command"],
            max_silence_minutes=int(item["max_silence_minutes"]),
            tags=item.get("tags", []),
        ))
    return rules


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def check_watchdog(rule: WatchdogRule, last_seen_iso: Optional[str]) -> WatchdogResult:
    if last_seen_iso is None:
        return WatchdogResult(
            command=rule.command,
            last_seen=None,
            silence_minutes=None,
            threshold_minutes=rule.max_silence_minutes,
            triggered=True,
            message=f"No run recorded for '{rule.command}'",
        )

    last_seen = datetime.fromisoformat(last_seen_iso)
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    silence = (_now_utc() - last_seen).total_seconds() / 60.0
    triggered = silence > rule.max_silence_minutes

    msg = (
        f"'{rule.command}' silent for {silence:.1f}m (threshold {rule.max_silence_minutes}m)"
        if triggered
        else f"'{rule.command}' OK — last seen {silence:.1f}m ago"
    )

    return WatchdogResult(
        command=rule.command,
        last_seen=last_seen_iso,
        silence_minutes=round(silence, 2),
        threshold_minutes=rule.max_silence_minutes,
        triggered=triggered,
        message=msg,
    )


def format_watchdog_result(result: WatchdogResult) -> str:
    status = "TRIGGERED" if result.triggered else "OK"
    return f"[watchdog:{status}] {result.message}"
