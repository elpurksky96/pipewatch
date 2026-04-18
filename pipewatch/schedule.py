"""Simple cron-style schedule checker for pipewatch."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ScheduleConfig:
    cron: str  # e.g. "*/5 * * * *" or "0 9 * * 1-5"
    timezone: str = "UTC"


def _field_matches(field: str, value: int, min_val: int, max_val: int) -> bool:
    """Check if a cron field matches a given value."""
    if field == "*":
        return True
    if re.fullmatch(r"\d+", field):
        return int(field) == value
    m = re.fullmatch(r"\*/(\d+)", field)
    if m:
        step = int(m.group(1))
        return (value - min_val) % step == 0
    m = re.fullmatch(r"(\d+)-(\d+)", field)
    if m:
        return int(m.group(1)) <= value <= int(m.group(2))
    if "," in field:
        return any(_field_matches(f.strip(), value, min_val, max_val) for f in field.split(","))
    return False


def is_due(schedule: ScheduleConfig, now: Optional[datetime] = None) -> bool:
    """Return True if the schedule is due at the given datetime (default: now)."""
    if now is None:
        now = datetime.utcnow()
    parts = schedule.cron.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {schedule.cron!r}")
    minute, hour, dom, month, dow = parts
    return (
        _field_matches(minute, now.minute, 0, 59)
        and _field_matches(hour, now.hour, 0, 23)
        and _field_matches(dom, now.day, 1, 31)
        and _field_matches(month, now.month, 1, 12)
        and _field_matches(dow, now.weekday(), 0, 6)
    )


def describe(schedule: ScheduleConfig) -> str:
    """Return a human-readable description of the schedule."""
    return f"cron({schedule.cron}) tz={schedule.timezone}"
