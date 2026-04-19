"""Time-window filtering for history entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional


@dataclass
class WindowConfig:
    hours: Optional[float] = None
    days: Optional[float] = None

    def total_seconds(self) -> Optional[float]:
        if self.hours is not None:
            return self.hours * 3600
        if self.days is not None:
            return self.days * 86400
        return None

    def describe(self) -> str:
        if self.days is not None:
            return f"last {self.days}d"
        if self.hours is not None:
            return f"last {self.hours}h"
        return "all time"


def _parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp, attaching UTC if naive."""
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def filter_by_window(entries: List, cfg: WindowConfig) -> List:
    """Return entries whose 'timestamp' field falls within the window.

    Entries without a timestamp attribute are passed through unchanged.
    """
    seconds = cfg.total_seconds()
    if seconds is None:
        return list(entries)

    cutoff = datetime.now(tz=timezone.utc) - timedelta(seconds=seconds)
    result = []
    for e in entries:
        ts_raw = getattr(e, "timestamp", None)
        if ts_raw is None:
            result.append(e)
            continue
        try:
            ts = _parse_timestamp(ts_raw)
        except (ValueError, TypeError):
            result.append(e)
            continue
        if ts >= cutoff:
            result.append(e)
    return result


def parse_window(value: Optional[str]) -> WindowConfig:
    """Parse a CLI string like '24h' or '7d' into a WindowConfig."""
    if not value:
        return WindowConfig()
    value = value.strip().lower()
    if value.endswith("h"):
        return WindowConfig(hours=float(value[:-1]))
    if value.endswith("d"):
        return WindowConfig(days=float(value[:-1]))
    raise ValueError(f"Unknown window format: {value!r}. Use e.g. '24h' or '7d'.")
