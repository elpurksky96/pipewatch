"""Alert suppression windows — silence alerts during known maintenance periods."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class SuppressionWindow:
    name: str
    start_iso: str
    end_iso: str
    commands: List[str] = field(default_factory=list)  # empty = all commands
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "start_iso": self.start_iso,
            "end_iso": self.end_iso,
            "commands": self.commands,
            "reason": self.reason,
        }

    @staticmethod
    def from_dict(d: dict) -> "SuppressionWindow":
        return SuppressionWindow(
            name=d.get("name", ""),
            start_iso=d["start_iso"],
            end_iso=d["end_iso"],
            commands=d.get("commands", []),
            reason=d.get("reason", ""),
        )

    def is_active(self, at: Optional[datetime] = None) -> bool:
        now = at or datetime.now(timezone.utc)
        start = datetime.fromisoformat(self.start_iso)
        end = datetime.fromisoformat(self.end_iso)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return start <= now <= end

    def covers_command(self, command: str) -> bool:
        return not self.commands or command in self.commands


def load_windows(path: Path) -> List[SuppressionWindow]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    return [SuppressionWindow.from_dict(d) for d in raw]


def save_windows(path: Path, windows: List[SuppressionWindow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([w.to_dict() for w in windows], indent=2))


def is_suppressed(
    command: str,
    windows: List[SuppressionWindow],
    at: Optional[datetime] = None,
) -> Optional[SuppressionWindow]:
    """Return the first active window that covers *command*, or None."""
    for w in windows:
        if w.is_active(at) and w.covers_command(command):
            return w
    return None


def describe_window(w: SuppressionWindow) -> str:
    parts = [f"[{w.name}] {w.start_iso} → {w.end_iso}"]
    if w.reason:
        parts.append(f"reason={w.reason!r}")
    if w.commands:
        parts.append(f"commands={w.commands}")
    else:
        parts.append("commands=all")
    return "  ".join(parts)
